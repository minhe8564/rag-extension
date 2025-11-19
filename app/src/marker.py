from __future__ import annotations

from .base import BaseExtractionStrategy
from typing import Dict, Any, List, Optional, Tuple
from loguru import logger
import os
import io
import json
import re
import tempfile
import base64
import shutil
from pathlib import Path

import requests

# 선택적 의존성
try:
    import fitz  # PyMuPDF for rasterizing PDF pages
except ImportError:
    fitz = None
    logger.warning("PyMuPDF not installed. PDF rasterization will not work.")

try:
    import numpy as np
    import cv2
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logger.warning("numpy/cv2 not available. Image cropping will be skipped.")

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    logger.warning("pandas not available. Table extraction will be limited.")

try:
    import pypdfium2 as pdfium
    PDFIUM_AVAILABLE = True
except ImportError:
    PDFIUM_AVAILABLE = False
    logger.warning("pypdfium2 not available. Table extraction will be limited.")

try:
    import camelot
    CAMELOT_AVAILABLE = True
except ImportError:
    CAMELOT_AVAILABLE = False
    logger.warning("camelot not available. Table extraction will be limited.")

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    logger.warning("pdfplumber not available. Table extraction will be limited.")

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("openai not available. Image captioning will be skipped.")

from app.service.minio_client import ensure_bucket, put_object_bytes
from app.core.settings import settings

# MARKER_BASE_URL과 YOLO_BASE_URL은 settings에서 동적으로 가져옴 (DB에서 업데이트됨)
# 모듈 레벨 상수 대신 함수 내에서 settings를 직접 참조
YOLO_CONF = float(os.getenv("YOLO_CONF", "0.4"))
DPI = int(os.getenv("MARKER_DPI", "200"))
ENABLE_CAPTIONS = os.getenv("ENABLE_CAPTIONS", "true").lower() == "true"

# 표 추출 튜닝
TABLE_MIN_AREA_PX = 18_000
TABLE_IOU_NMS = 0.4
MAX_TABLE_AREAS_PER_PAGE = 30

# 파일명 정규화
_RID_PREFIX = re.compile(r"^[0-9a-f]{32}_", re.IGNORECASE)


def _stem_without_rid(stem: str) -> str:
    """파일 스템에서 RID(32 hex + '_')를 제거."""
    return _RID_PREFIX.sub("", stem)


def _sanitize_stem(stem: str) -> str:
    """안전한 스템: RID 제거 → 공백을 '_' → 금지문자 제거."""
    s = _stem_without_rid(stem).strip().replace(" ", "_")
    s = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "", s)
    s = re.sub(r"\.+$", "", s)
    return s


def _make_uid_and_base(stem: str, page: int, kind: str, idx: int) -> Tuple[str, str]:
    """UID/베이스명 생성."""
    assert kind in ("fig", "tbl")
    uid = f"{stem}#p{page:03d}:{kind}:{idx:03d}"
    base = f"{stem}-p{page:03d}-{'fig' if kind=='fig' else 'tbl'}{idx:03d}"
    return uid, base


def _safe_write_text(path: Path, text: str, encoding: str = "utf-8") -> None:
    """부모 디렉터리 자동 생성 후 텍스트 저장."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding=encoding)


def _iou_xyxy(a: Tuple[int, int, int, int], b: Tuple[int, int, int, int]) -> float:
    """IoU for two xyxy boxes."""
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    iw = max(0, min(ax2, bx2) - max(ax1, bx1))
    ih = max(0, min(ay2, by2) - max(ay1, by1))
    inter = iw * ih
    if inter <= 0:
        return 0.0
    area_a = max(0, ax2 - ax1) * max(0, ay2 - ay1)
    area_b = max(0, bx2 - bx1) * max(0, by2 - by1)
    denom = area_a + area_b - inter
    return inter / denom if denom > 0 else 0.0


class Marker(BaseExtractionStrategy):
    """
    Marker 원격 파이프라인 (run_pipeline_remote 기반):
      run_pipeline_remote.py의 모든 기능 구현:
      1) 모든 입력(PDF/비-PDF)을 Marker에 업로드 -> markdown 수신
      2) PDF 경로 확보 (PDF면 원본, 비-PDF면 presigned_url로 다운로드)
      3) PDF 렌더링 (PyMuPDF) -> page PNG 이미지 생성
      4) YOLO(bboxes) 호출 -> 표/이미지 바운딩박스 검출
      5) 표 추출 (Camelot/pdfplumber)
      6) clean.md 생성 (Marker 텍스트 + 표 병합)
      7) 이미지 캡션 생성 (OpenAI)
      8) final.md 생성 (PLACEHOLDER 치환, 캡션 포함)
      9) manifest 생성
      10) MinIO 업로드 (final.md, 캡션)
    """

    def _call_marker_extract_md(self, file_path: str) -> Dict[str, Any]:
        """Marker extract-md API 호출 (PDF/비-PDF 모두 지원)"""
        url = f"{settings.marker_provider_url}/api/v1/marker/extract-md"
        logger.info(f"[Marker] POST {url} | file={os.path.basename(file_path)}")
        filename = os.path.basename(file_path)
        with open(file_path, "rb") as f:
            files = {"file": (filename, f, "application/octet-stream")}
            resp = requests.post(url, files=files, timeout=600.0)
            resp.raise_for_status()
            return resp.json()

    def _ensure_pdf_path_sync(self, file_path: str, marker_response: Optional[Dict[str, Any]]) -> str:
        """비-PDF 입력에 대해 marker_response에서 presigned_url 추출 후 PDF 다운로드"""
        presigned_url = None
        try:
            if isinstance(marker_response, dict):
                presigned_url = (
                    marker_response.get("result", {})
                    .get("data", {})
                    .get("presigned_url")
                ) or marker_response.get("presigned_url")
        except Exception:
            presigned_url = None

        if not presigned_url:
            # fallback: marker의 convert-to-pdf 사용
            try:
                url = f"{settings.marker_provider_url}/api/v1/marker/convert-to-pdf"
                filename = os.path.basename(file_path)
                with open(file_path, "rb") as f:
                    files = {"file": (filename, f, "application/octet-stream")}
                    r = requests.post(url, files=files, timeout=600.0)
                    r.raise_for_status()
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        tmp.write(r.content)
                        return tmp.name
            except Exception as e:
                raise RuntimeError(f"Failed to convert non-PDF via marker: {e}")

        # presigned_url로 PDF 다운로드
        try:
            r = requests.get(presigned_url, timeout=600.0)
            r.raise_for_status()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(r.content)
                return tmp.name
        except Exception as e:
            raise RuntimeError(f"Failed to download PDF via presigned_url: {e}")

    def _render_pdf_to_images(self, pdf_path: str, dpi: int = DPI) -> List[Tuple[int, np.ndarray]]:
        """PDF를 PNG 이미지로 렌더링 (페이지 번호, BGR 배열 반환)"""
        if fitz is None:
            raise ImportError("PyMuPDF(fitz) is required to rasterize PDF pages.")
        if not NUMPY_AVAILABLE:
            raise ImportError("numpy/cv2 is required for image rendering.")
        
        doc = fitz.open(pdf_path)
        try:
            images: List[Tuple[int, np.ndarray]] = []
            scale = dpi / 72.0
            for i in range(len(doc)):
                page = doc[i]
                mat = fitz.Matrix(scale, scale)
                pix = page.get_pixmap(matrix=mat, alpha=False)
                # PyMuPDF는 RGB, cv2는 BGR 사용
                img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
                if pix.n == 3:  # RGB
                    img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                else:
                    img_bgr = img_array
                images.append((i + 1, img_bgr))
            return images
        finally:
            doc.close()

    def _call_yolo_bboxes(self, images: List[Tuple[int, np.ndarray]], conf: float = YOLO_CONF) -> List[Dict[str, Any]]:
        """YOLO 서비스 호출"""
        url = f"{settings.yolo_provider_url}/api/v1/yolo/detect-bboxes"
        pages = []
        files = []
        
        for pno, bgr in images:
            ok, buf = cv2.imencode(".png", bgr)
            if not ok:
                raise RuntimeError(f"failed to encode page {pno} to PNG")
            files.append(("images", (f"p{pno}.png", buf.tobytes(), "image/png")))
            pages.append(pno)
        
        data = {"pages_json": json.dumps(pages), "conf": str(conf)}
        logger.info(f"[YOLO] POST {url} | n_pages={len(pages)}, conf={conf}")
        resp = requests.post(url, data=data, files=files, timeout=600.0)
        resp.raise_for_status()
        js = resp.json()
        # Accept multiple envelope formats:
        # - { status, code, isSuccess, result: { data: { detections: [...] } } }
        # - { state: "success", data: { detections: [...] } }
        # - { detections: [...] }
        is_success = False
        try:
            if js.get("isSuccess") is True:
                is_success = True
            elif str(js.get("status")) == "200":
                is_success = True
            elif str(js.get("code", "")).upper() in {"SUCCESS", "OK"}:
                is_success = True
            elif js.get("state") == "success":
                is_success = True
        except Exception:
            is_success = False

        # Extract detections
        detections = (
            js.get("result", {}).get("data", {}).get("detections")
            or js.get("data", {}).get("detections")
            or js.get("detections")
        )
        if detections is None:
            detections = []

        if not is_success:
            # Treat as soft failure only if explicitly unsuccessful
            raise RuntimeError(f"yolo failed: {js}")
        return detections

    def _clamp_xyxy(self, x1: int, y1: int, x2: int, y2: int, w: int, h: int) -> Tuple[int, int, int, int]:
        """bbox 좌표를 이미지 범위 내로 제한"""
        x1 = max(0, min(x1, w - 1))
        y1 = max(0, min(y1, h - 1))
        x2 = max(0, min(x2, w))
        y2 = max(0, min(y2, h))
        return x1, y1, x2, y2

    def _strip_marker_tables(self, md: str) -> str:
        """Marker 출력에서 표 블록 제거 (후처리)"""
        blocks = re.split(r"\n{2,}", md)
        keep = []
        for b in blocks:
            lines = b.splitlines()
            pipe_ratio = (sum(1 for ln in lines if '|' in ln) / max(1, len(lines)))
            avg_pipes = (sum(ln.count('|') for ln in lines) / max(1, len(lines)))
            looks_table = pipe_ratio >= 0.5 and avg_pipes >= 4
            sep_like = any(re.search(r"\|\s*:?-{3,}\s*(:?\|)?", ln) for ln in lines[:3])
            if looks_table or sep_like:
                continue
            keep.append(b)
        return "\n\n".join(keep)

    def _strip_marker_htmlish(self, md: str) -> str:
        """Marker 출력에서 HTML 태그 제거"""
        md = re.sub(r'(?s)(?<!`)<(table|ul|ol)\b[^>]*>.*?</\1>', '', md, flags=re.IGNORECASE)
        lines, out, li_run = md.splitlines(), [], []
        def flush():
            nonlocal out, li_run
            if len(li_run) >= 3:
                li_run = []
                return
            out.extend(li_run)
            li_run = []
        for ln in lines:
            if re.search(r'^\s*<li\b[^>]*>.*?</li>\s*$', ln, flags=re.IGNORECASE):
                li_run.append(ln)
            else:
                flush()
                out.append(ln)
        flush()
        md = "\n".join(out)
        md = re.sub(r'(?m)^\s*</?(li|tr|td|th)>\s*$', '', md, flags=re.IGNORECASE)
        md = re.sub(r'\n{3,}', '\n\n', md).strip()
        return md

    def _process_detections(self, detections: List[Dict[str, Any]], images: List[Tuple[int, np.ndarray]], safe_stem: str, temp_dir: Path) -> List[Dict[str, Any]]:
        """YOLO 감지 결과를 처리하여 det_items 생성 (크롭 이미지 저장 포함)"""
        det_items: List[Dict[str, Any]] = []
        crop_dir = temp_dir / "crop_imgs"
        crop_dir.mkdir(parents=True, exist_ok=True)
        
        by_page = {pno: img for pno, img in images}
        
        for det in detections:
            pno = int(det.get("page", 0))
            im = by_page.get(pno)
            if im is None:
                continue
            
            H, W = im.shape[:2]
            for i, it in enumerate(det.get("items", []), start=1):
                lb = str(it.get("cls", "")).lower()
                if lb not in {"figure", "table"}:
                    continue
                kind = "fig" if lb == "figure" else "tbl"
                x1, y1, x2, y2 = map(int, it.get("bbox", [0, 0, 0, 0]))
                x1, y1, x2, y2 = self._clamp_xyxy(x1, y1, x2, y2, W, H)
                uid, base = _make_uid_and_base(safe_stem, pno, kind, i)

                file_path = None
                if kind == "fig" and NUMPY_AVAILABLE:
                    crop = im[y1:y2, x1:x2]
                    if crop is not None and crop.size > 0:
                        if crop.dtype != np.uint8:
                            crop = np.clip(crop, 0, 255).astype(np.uint8)
                        out_png = crop_dir / f"{base}.png"
                        cv2.imwrite(str(out_png), crop)
                        file_path = str(out_png)

                det_items.append({
                    "page": pno,
                    "idx": i,
                    "cls": lb,
                    "conf": float(it.get("conf", 0.0)),
                    "bbox": (x1, y1, x2, y2),
                    "kind": kind,
                    "uid": uid,
                    "file_path": file_path,
                })
        
        return det_items

    def _dedupe_table_boxes(self, det_items: List[Dict[str, Any]], min_area: int, iou_thr: float, max_per_page: int) -> Dict[int, List[Dict[str, Any]]]:
        """table만 추려서 너무 작은 bbox 제거 후 간단 NMS로 중복 제거"""
        by_page: Dict[int, List[Dict[str, Any]]] = {}
        for d in det_items:
            if d.get("kind") != "tbl":
                continue
            x1, y1, x2, y2 = d["bbox"]
            if (x2 - x1) * (y2 - y1) < min_area:
                continue
            by_page.setdefault(d["page"], []).append(d)

        result: Dict[int, List[Dict[str, Any]]] = {}
        for p, items in by_page.items():
            items = sorted(items, key=lambda x: (x["bbox"][2]-x["bbox"][0])*(x["bbox"][3]-x["bbox"][1]), reverse=True)
            kept: List[Dict[str, Any]] = []
            for it in items:
                if any(_iou_xyxy(it["bbox"], k["bbox"]) > iou_thr for k in kept):
                    continue
                kept.append(it)
                if len(kept) >= max_per_page:
                    break
            kept.sort(key=lambda d: (d["bbox"][1], d["bbox"][0]))
            result[p] = kept
        return result

    def _extract_tables_from_yolo(self, pdf_path: str, det_items: List[Dict[str, Any]], temp_dir: Path, safe_stem: str, dpi: int) -> Optional[Path]:
        """YOLO가 반환한 table bbox만 이용해 실제 표를 추출하고 저장"""
        if not PDFIUM_AVAILABLE:
            return None

        # 작은 table 제거 + NMS
        tbl_by_page = self._dedupe_table_boxes(
            det_items, min_area=TABLE_MIN_AREA_PX, iou_thr=TABLE_IOU_NMS, max_per_page=MAX_TABLE_AREAS_PER_PAGE
        )
        if not any(tbl_by_page.values()):
            return None

        # 집계 파일 경로
        text_dir = temp_dir / "text"
        text_dir.mkdir(parents=True, exist_ok=True)
        agg_md_path = text_dir / f"{safe_stem}-tables.md"
        agg_lines = [f"# Tables from YOLO regions ({safe_stem})\n"]

        doc = pdfium.PdfDocument(pdf_path)
        plumber_doc = pdfplumber.open(pdf_path) if PDFPLUMBER_AVAILABLE else None

        zoom = dpi / 72.0
        total_saved = 0

        for pno in sorted(tbl_by_page.keys()):
            items = tbl_by_page[pno]
            if not items:
                continue

            agg_lines.append(f"\n## Page {pno}\n")
            pw_pt, ph_pt = doc[pno - 1].get_size()
            sorted_items = sorted(items, key=lambda d: d["bbox"][1])
            
            areas: List[str] = []
            for i, d in enumerate(sorted_items):
                x1, y1, x2, y2 = d["bbox"]
                bx1, by1, bx2, by2 = x1/zoom, y1/zoom, x2/zoom, y2/zoom
                pdf_y1 = ph_pt - by2
                pdf_y2 = ph_pt - by1
                areas.append(f"{bx1},{pdf_y1},{bx2},{pdf_y2}")

            extracted_dfs: List[pd.DataFrame] = []

            # Camelot lattice 우선
            if CAMELOT_AVAILABLE:
                try:
                    if areas:
                        tables = camelot.read_pdf(
                            pdf_path, pages=str(pno), flavor="lattice",
                            table_areas=areas, line_scale=20, strip_text="\n"
                        )
                        for t in tables or []:
                            if hasattr(t, "df") and not t.df.empty:
                                extracted_dfs.append(t.df)
                    else:
                        logger.debug(f"Camelot lattice 건너뜀(page {pno}): table_areas 비어 있음")
                except Exception as e:
                    # 일부 PDF 페이지에서 내부적으로 빈 시퀀스 max() 등이 발생할 수 있음 → 경고 대신 정보로 스킵
                    logger.info(f"Camelot lattice 스킵(page {pno}): {e}")

                # stream 시도
                if not extracted_dfs:
                    try:
                        if areas:
                            tables2 = camelot.read_pdf(
                                pdf_path, pages=str(pno), flavor="stream",
                                table_areas=areas, edge_tol=100, row_tol=20, strip_text="\n"
                            )
                            for t in tables2 or []:
                                if hasattr(t, "df") and not t.df.empty:
                                    extracted_dfs.append(t.df)
                        else:
                            logger.debug(f"Camelot stream 건너뜀(page {pno}): table_areas 비어 있음")
                    except Exception as e:
                        # 빈 시퀀스 max() 등의 예외는 스킵 (표 미검출로 처리)
                        logger.info(f"Camelot stream 스킵(page {pno}): {e}")

            # pdfplumber 폴백
            if not extracted_dfs and plumber_doc:
                try:
                    page_plumber = plumber_doc.pages[pno - 1]
                    for i, d in enumerate(sorted_items):
                        x1, y1, x2, y2 = d["bbox"]
                        bx1, by1, bx2, by2 = x1/zoom, y1/zoom, x2/zoom, y2/zoom
                        bbox_plumber = (bx1, ph_pt - by2, bx2, ph_pt - by1)
                        cropped = page_plumber.crop(bbox_plumber)
                        tbls = cropped.extract_tables(table_settings=dict(
                            vertical_strategy="lines",
                            horizontal_strategy="lines",
                            snap_tolerance=3,
                            join_tolerance=3,
                            edge_min_length=3,
                            min_words_vertical=1,
                            min_words_horizontal=1,
                            intersection_tolerance=3,
                        )) or []
                        for t in tbls:
                            df = pd.DataFrame(t[1:], columns=t[0]) if t and t[0] else pd.DataFrame(t)
                            if not df.empty:
                                extracted_dfs.append(df)
                except Exception as e:
                    logger.warning(f"pdfplumber 추출 실패(page {pno}): {e}")

            # 저장
            for i, df in enumerate(extracted_dfs, 1):
                _, base = _make_uid_and_base(safe_stem, pno, "tbl", i)
                mdp = text_dir / f"{base}.md"
                csvp = text_dir / f"{base}.csv"
                try:
                    md_text = df.to_markdown(index=False)
                except Exception:
                    try:
                        md_text = df.to_csv(index=False)
                    except Exception:
                        md_text = df.to_string(index=False)
                _safe_write_text(mdp, md_text)
                try:
                    if PANDAS_AVAILABLE:
                        df.to_csv(csvp, index=False, encoding="utf-8-sig")
                except Exception as e:
                    logger.warning(f"CSV 저장 실패({csvp}): {e}")
                agg_lines.append(f"\n### Table {i}\n{md_text}\n")
                total_saved += 1

        if plumber_doc:
            try:
                plumber_doc.close()
            except Exception:
                pass

        if total_saved:
            _safe_write_text(agg_md_path, "\n".join(agg_lines))
            logger.info(f"YOLO 영역 기반 표 저장: {agg_md_path} (총 {total_saved}개)")
            return agg_md_path
        return None

    def _save_clean_markdown(self, marker_md_path: Path, table_md_path: Optional[Path], temp_dir: Path, safe_stem: str) -> Optional[Path]:
        """Marker 본문 + 표 집계 파일을 한데 모아 'clean.md' 생성"""
        if not marker_md_path.exists() and not table_md_path:
            return None

        lines: List[str] = [f"# {safe_stem} (clean)\n"]
        if marker_md_path.exists():
            lines += ["## Main Text (from Marker)\n", marker_md_path.read_text(encoding="utf-8")]
        if table_md_path and table_md_path.exists():
            lines += ["\n---\n\n## Tables (from YOLO)\n", table_md_path.read_text(encoding="utf-8")]

        text_dir = temp_dir / "text"
        clean_path = text_dir / f"{safe_stem}-clean.md"
        _safe_write_text(clean_path, "\n".join(lines))
        return clean_path

    def _b64_of_image(self, path: str) -> str:
        """이미지를 base64로 변환"""
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def _qwen3_caption_one_image(self, image_path: str, lang: str = "ko") -> Tuple[str, Dict[str, int]]:
        """Qwen3 (Ollama)를 사용하여 단일 이미지에 대해 캡션 생성 (fallback)"""
        try:
            import httpx
            base_url = settings.qwen_base_url.rstrip("/")
            url = f"{base_url}/api/chat"
            
            b64 = self._b64_of_image(image_path)
            sys_prompt = (
                f"당신은 과학 문서 전문 기술 작가입니다. "
                f"{lang}로 간결하고 정확한 캡션을 작성하세요. "
                f"불확실한 경우 시각적으로 관찰 가능한 요소만 설명하세요."
            )
            user_prompt = "이미지를 보고 핵심 내용만 1~2문장으로 설명해 주세요. (단위/축/범례/구성요소가 보이면 언급)"
            
            payload = {
                "model": "qwen3-vl:8b",
                "messages": [
                    {
                        "role": "system",
                        "content": sys_prompt
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": user_prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{b64}"
                                }
                            }
                        ]
                    }
                ],
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "num_predict": 180
                }
            }
            
            with httpx.Client(timeout=120.0) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                result = response.json()
                
                if "message" in result:
                    message = result["message"]
                    caption = message.get("content", "").strip()
                    usage_dict = {
                        "prompt_tokens": 0,  # Ollama는 토큰 사용량을 직접 제공하지 않을 수 있음
                        "completion_tokens": 0,
                        "total_tokens": 0,
                    }
                    return caption, usage_dict
                else:
                    logger.warning(f"Qwen3 응답 형식 오류: {result}")
                    return "", {}
        except Exception as e:
            logger.warning(f"Qwen3 caption 실패({image_path}): {e}")
            return "", {}
    
    def _openai_caption_one_image(self, image_path: str, lang: str = "ko", model: str = "gpt-4o") -> Tuple[str, Dict[str, int]]:
        """단일 이미지에 대해 캡션 생성 (OpenAI 우선, 실패 시 Qwen3 fallback)"""
        if not OPENAI_AVAILABLE:
            logger.info("OpenAI not available, using Qwen3 fallback")
            return self._qwen3_caption_one_image(image_path, lang=lang)
        
        try:
            client = OpenAI()
            b64 = self._b64_of_image(image_path)
            sys_prompt = (
                f"You are an expert technical writer for scientific documents. "
                f"Write a concise, precise caption in {lang}. "
                f"Avoid hallucinations; if uncertain, describe visually observable elements only."
            )
            user_prompt = "이미지를 보고 핵심 내용만 1~2문장으로 설명해 주세요. (단위/축/범례/구성요소가 보이면 언급)"
            
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                        ],
                    },
                ],
                temperature=0.2,
                max_tokens=180,
            )
            caption = (resp.choices[0].message.content or "").strip()
            usage = getattr(resp, "usage", None)
            usage_dict = {
                "prompt_tokens": getattr(usage, "prompt_tokens", 0) or 0,
                "completion_tokens": getattr(usage, "completion_tokens", 0) or 0,
                "total_tokens": getattr(usage, "total_tokens", 0) or 0,
            }
            return caption, usage_dict
        except Exception as e:
            # TPM 문제나 기타 OpenAI 오류 시 Qwen3 fallback 사용
            error_msg = str(e).lower()
            is_tpm_error = "tpm" in error_msg or "rate limit" in error_msg or "quota" in error_msg
            if is_tpm_error:
                logger.warning(f"OpenAI TPM/quota 오류 감지, Qwen3 fallback 사용: {e}")
            else:
                logger.warning(f"OpenAI caption 실패, Qwen3 fallback 사용: {e}")
            
            # Qwen3 fallback 시도
            try:
                return self._qwen3_caption_one_image(image_path, lang=lang)
            except Exception as fallback_error:
                logger.error(f"Qwen3 fallback도 실패({image_path}): {fallback_error}")
                return "", {}

    def _caption_figures(self, det_items: List[Dict[str, Any]], cache_path: Path, lang: str = "ko", model: str = "gpt-4o") -> Tuple[Dict[str, str], Dict[str, Any]]:
        """figure 자산들에 대해 캡션을 생성"""
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}
        except Exception:
            cache = {}

        captions: Dict[str, str] = {}
        stats = {
            "images_total": 0,
            "images_captions": 0,
            "images_skipped": 0,
            "tokens_prompt": 0,
            "tokens_completion": 0,
            "tokens_total": 0,
            "model": model,
            "lang": lang,
        }

        for d in det_items:
            if d.get("kind") != "fig" or not d.get("file_path"):
                continue

            stats["images_total"] += 1
            key = d.get("uid") or f"p{d['page']:03d}-fig{d['idx']:03d}"

            if key in cache and cache[key]:
                captions[key] = cache[key]
                stats["images_captions"] += 1
                continue

            cap, usage = self._openai_caption_one_image(d["file_path"], lang=lang, model=model)

            if cap:
                cache[key] = cap
                captions[key] = cap
                stats["images_captions"] += 1
                stats["tokens_prompt"] += usage.get("prompt_tokens", 0)
                stats["tokens_completion"] += usage.get("completion_tokens", 0)
                stats["tokens_total"] += usage.get("total_tokens", 0)
                try:
                    cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
                except Exception as e:
                    logger.warning(f"캡션 캐시 저장 실패: {e}")
            else:
                stats["images_skipped"] += 1

        return captions, stats

    def _save_final_markdown(self, marker_md_path: Path, det_items: List[Dict[str, Any]], temp_dir: Path, safe_stem: str, captions: Dict[str, str]) -> Path:
        """Marker가 내보낸 마크다운 속 이미지 태그를 PLACEHOLDER로 치환"""
        text_dir = temp_dir / "text"
        final_md_path = text_dir / f"{safe_stem}-final.md"

        if not marker_md_path.exists():
            _safe_write_text(final_md_path, f"# {safe_stem}\n(Marker 결과 없음)")
            return final_md_path

        original_md_text = marker_md_path.read_text(encoding="utf-8")

        page_figs: Dict[int, List[Dict[str, Any]]] = {}
        for it in det_items:
            if it.get("kind") == "fig":
                page_figs.setdefault(it["page"], []).append(it)
        for p in page_figs:
            page_figs[p].sort(key=lambda it: (it["bbox"][1], it["bbox"][0]))

        page_counters = {p: 0 for p in page_figs.keys()}

        def _esc(s: str) -> str:
            return (s or "").replace("\n", " ").replace('"', '\\"')

        def replacer(m):
            try:
                z = int(m.group(1))
                p_num = z + 1
                if p_num in page_figs:
                    ci = page_counters[p_num]
                    if ci < len(page_figs[p_num]):
                        it = page_figs[p_num][ci]
                        page_counters[p_num] += 1
                        _, base = _make_uid_and_base(safe_stem, it["page"], it["kind"], it["idx"])
                        cap_key = it.get("uid") or base
                        desc = _esc(captions.get(cap_key, ""))
                        return f'\n\n<<<PLACEHOLDER|{it["kind"]}|{base}|desc="{desc}">>>\n\n'
            except Exception as e:
                logger.warning(f"이미지 태그 치환 오류: {e}")
            return ""

        final_text = re.sub(r"!\[[^\]]*\]\(_page_(\d+)_", replacer, original_md_text)
        final_text = re.sub(r"\n{3,}", "\n\n", final_text).strip()

        # Remove stray figure filename lines like "Figure_0.jpeg)" or "Picture_11.jpeg)"
        try:
            final_text = re.sub(
                r"^[ \t]*(?:Figure|Picture)_[^)]+?\.(?:png|jpe?g|webp|gif)\)[ \t]*$",
                "",
                final_text,
                flags=re.IGNORECASE | re.MULTILINE,
            )
            # Normalize spacing again after removal
            final_text = re.sub(r"\n{3,}", "\n\n", final_text).strip()
        except Exception:
            pass

        _safe_write_text(final_md_path, final_text)
        return final_md_path

    def _save_manifest(self, pdf_path: str, det_items: List[Dict[str, Any]], temp_dir: Path, safe_stem: str, dpi: int, captions: Dict[str, str]) -> Path:
        """figure/table 자산들에 대한 메타 정보를 JSON으로 저장"""
        manifests_dir = temp_dir / "manifests"
        manifests_dir.mkdir(parents=True, exist_ok=True)

        manifest: Dict[str, Any] = {
            "version": "1.0",
            "pdf": pdf_path,
            "stem": safe_stem,
            "dpi": dpi,
            "units": {
                "bbox": "pixel_xyxy",
                "page": "pt@72dpi",
            },
            "assets": {}
        }

        for d in det_items:
            uid, base = _make_uid_and_base(safe_stem, d["page"], d["kind"], d["idx"])
            manifest["assets"][uid] = {
                "page": d["page"],
                "idx": d["idx"],
                "kind": d["kind"],
                "label": d["cls"],
                "conf": d["conf"],
                "bbox_xyxy_pixel": list(map(int, d["bbox"])),
                "file_base": base,
                "file_path": d.get("file_path"),
                "caption": captions.get(uid, ""),
            }

        out = manifests_dir / f"{safe_stem}-manifest.json"
        _safe_write_text(out, json.dumps(manifest, ensure_ascii=False, indent=2))
        return out

    def extract(self, file_path: str) -> Dict[str, Any]:
        """
        run_pipeline_remote 흐름 완전 구현:
          1) Marker 호출 (모든 입력) → markdown
          2) PDF 경로 확보 (비-PDF면 presigned_url로 다운로드)
          3) PDF 렌더링 → PNG 이미지
          4) YOLO 호출 → 바운딩 박스
          5) 표 추출 (Camelot/pdfplumber)
          6) clean.md 생성
          7) 이미지 캡션 생성 (OpenAI)
          8) final.md 생성 (PLACEHOLDER 치환, 캡션 포함)
          9) manifest 생성
          10) MinIO 업로드 (final.md, 캡션)
        """
        logger.info(f"[MarkerStrategy] Starting pipeline for: {file_path}")

        # 진행률 콜백
        progress_cb = None
        try:
            progress_cb = self.parameters.get("progress_cb") if isinstance(self.parameters, dict) else None
        except Exception:
            progress_cb = None
        if progress_cb:
            try:
                progress_cb(0, None)
            except Exception:
                pass

        # 임시 디렉터리 생성
        temp_dir = Path(tempfile.mkdtemp(prefix="marker_"))
        converted_pdf_path = None

        try:
            # 1) Marker 호출 (모든 입력에 대해)
            marker_resp = self._call_marker_extract_md(file_path)
            logger.info(f"[Marker] Response received")

            # markdown 텍스트 추출
            md_text = None
            try:
                md_text = (
                    marker_resp.get("result", {})
                    .get("data", {})
                    .get("markdown")
                ) or marker_resp.get("markdown")
            except Exception:
                md_text = None

            if not md_text:
                raise RuntimeError("Failed to extract markdown from Marker response")

            # Marker 후처리
            md_text = self._strip_marker_tables(md_text)
            md_text = self._strip_marker_htmlish(md_text)

            # Marker 본문 저장
            safe_stem = _sanitize_stem(Path(file_path).stem)
            text_dir = temp_dir / "text"
            text_dir.mkdir(parents=True, exist_ok=True)
            marker_md_path = text_dir / f"{safe_stem}.md"
            _safe_write_text(marker_md_path, md_text)

            # 2) PDF 경로 확보 (비-PDF면 presigned_url로 다운로드)
            ext = os.path.splitext(file_path)[1].lower()
            if ext == ".pdf":
                pdf_path = file_path
            else:
                pdf_path = self._ensure_pdf_path_sync(file_path, marker_resp)
                converted_pdf_path = pdf_path
                logger.info(f"[PDF] Downloaded converted PDF from presigned_url: {pdf_path}")

            # 3) PDF 렌더링
            images = self._render_pdf_to_images(pdf_path, dpi=DPI)
            logger.info(f"[Render] Rendered {len(images)} pages")

            # 4) YOLO 호출
            detections = self._call_yolo_bboxes(images, conf=YOLO_CONF)
            logger.info(f"[YOLO] Detected {len(detections)} pages with objects")

            # 5) 감지 결과 처리 (크롭 이미지 저장)
            det_items = self._process_detections(detections, images, safe_stem, temp_dir)
            logger.info(f"[Detections] Processed {len(det_items)} items")

            # 6) 표 추출
            table_md_path = self._extract_tables_from_yolo(pdf_path, det_items, temp_dir, safe_stem, DPI)
            if table_md_path:
                logger.info(f"[Tables] Extracted tables: {table_md_path}")

            # 7) clean.md 생성
            clean_md_path = self._save_clean_markdown(marker_md_path, table_md_path, temp_dir, safe_stem)
            if clean_md_path:
                logger.info(f"[Clean] Created clean.md: {clean_md_path}")

            # 8) 이미지 캡션 생성
            captions: Dict[str, str] = {}
            if ENABLE_CAPTIONS and OPENAI_AVAILABLE:
                cap_cache = temp_dir / "manifests" / f"{safe_stem}-captions.json"
                captions, cap_stats = self._caption_figures(det_items, cap_cache, lang="ko", model="gpt-4o")
                logger.info(f"[Captions] Generated {cap_stats['images_captions']}/{cap_stats['images_total']} captions")
            else:
                logger.info("[Captions] Skipped (disabled or OpenAI not available)")

            # 9) final.md 생성 (clean_md가 있으면 사용, 없으면 marker_md_path 사용)
            final_source = clean_md_path if clean_md_path and clean_md_path.exists() else marker_md_path
            final_md_path = self._save_final_markdown(final_source, det_items, temp_dir, safe_stem, captions)
            logger.info(f"[Final] Created final.md: {final_md_path}")

            # 10) manifest 생성
            manifest_path = self._save_manifest(pdf_path, det_items, temp_dir, safe_stem, DPI, captions)
            logger.info(f"[Manifest] Created manifest: {manifest_path}")

            # 11) MinIO 업로드
            user_id = self.parameters.get("user_id", "unknown-user") if isinstance(self.parameters, dict) else "unknown-user"
            file_name = self.parameters.get("file_name", "output.txt") if isinstance(self.parameters, dict) else "output.txt"
            base_name = Path(file_name).stem
            
            # final.md 업로드 (텍스트가 아니라 md 확장자로 저장)
            final_md_text = final_md_path.read_text(encoding="utf-8")
            object_name = f"{user_id}/{base_name}.md"
            bucket_name = "ingest"
            
            ensure_bucket(bucket_name)
            put_object_bytes(
                bucket_name=bucket_name,
                object_name=object_name,
                data=final_md_text.encode("utf-8"),
                content_type="text/markdown; charset=utf-8"
            )
            logger.info(f"[MinIO] Uploaded final.md to {bucket_name}/{object_name}")

            # 감지된 figure 이미지 업로드 (crop 저장된 PNG)
            uploaded_images: List[Dict[str, Any]] = []
            try:
                import hashlib
                # 원본 파일명 가져오기 (확장자 제거)
                original_file_name = self.parameters.get("file_name", "") if isinstance(self.parameters, dict) else ""
                original_doc_name = Path(original_file_name).stem if original_file_name else safe_stem
                
                # figure만 필터링하고 순서대로 번호 부여
                figure_items = [it for it in det_items if it.get("kind") == "fig" and it.get("file_path")]
                figure_counter = 1
                
                for it in figure_items:
                    fp = it.get("file_path")
                    if not fp:
                        continue
                    try:
                        name_only = Path(fp).name  # MinIO 저장용 (기존 형식 유지)
                        obj_img = f"{user_id}/{name_only}"
                        with open(fp, "rb") as fimg:
                            img_bytes = fimg.read()
                        put_object_bytes(
                            bucket_name=bucket_name,
                            object_name=obj_img,
                            data=img_bytes,
                            content_type="image/png"
                        )
                        sha = hashlib.sha256(img_bytes).hexdigest()
                        
                        # DB 저장용 이름 생성: 원본문서명-fig001.png 형식
                        db_name = f"{original_doc_name}-fig{figure_counter:03d}.png"
                        figure_counter += 1
                        
                        uploaded_images.append({
                            "uid": it.get("uid"),
                            "name": name_only,  # MinIO용 (기존 형식)
                            "db_name": db_name,  # DB용 (원본 문서명 기반)
                            "object_name": obj_img,
                            "bucket": bucket_name,
                            "size": len(img_bytes),
                            "hash": sha,
                            "type": "png",
                            "page": it.get("page"),
                            "idx": it.get("idx"),
                        })
                    except Exception as ue:
                        logger.warning(f"[MinIO] Image upload failed for {fp}: {ue}")
            except Exception as e:
                logger.warning(f"[MinIO] Image upload loop error: {e}")

            # 캡션을 MinIO에 별도 저장 (JSON)
            if captions:
                captions_object_name = f"{user_id}/{base_name}_captions.json"
                put_object_bytes(
                    bucket_name=bucket_name,
                    object_name=captions_object_name,
                    data=json.dumps(captions, ensure_ascii=False, indent=2).encode("utf-8"),
                    content_type="application/json; charset=utf-8"
                )
                logger.info(f"[MinIO] Uploaded captions to {bucket_name}/{captions_object_name}")
            
            # 진행률 완료
            if progress_cb:
                try:
                    progress_cb(len(images), len(images))
                except Exception:
                    pass

            return {
                "full_text": final_md_text,
                "bucket": bucket_name,
                "path": object_name,
                "type": "marker",
                "total_pages": len(images),
                "detections": len(det_items),
                "captions": captions,
                "images": uploaded_images,
            }

        finally:
            # 임시 파일 정리
            try:
                if converted_pdf_path and os.path.exists(converted_pdf_path):
                    os.unlink(converted_pdf_path)
            except Exception:
                pass
            try:
                if temp_dir.exists():
                    shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass
