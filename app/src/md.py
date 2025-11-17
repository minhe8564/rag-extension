from __future__ import annotations

from .base import BaseChunkingStrategy
from typing import List, Dict, Any, Tuple, Optional
from loguru import logger
import re
import httpx

try:
    from transformers import AutoTokenizer
except ImportError:
    AutoTokenizer = None
    logger.warning("transformers not installed. Markdown chunking will not work.")


# ---------- 정규식 패턴 ----------
_HEADING = re.compile(r'^(#{1,6})\s+(.*)$')   # "# ..." ~ "###### ..."
_CODEFENCE = re.compile(r'^```')              # fenced code
_MATH_FENCE = re.compile(r'^\$\$')            # fenced math

_TABLE_LINE = re.compile(r'^\s*\|.*\|\s*$')
def _is_table_line(line: str) -> bool:
    if _TABLE_LINE.match(line):
        return True
    return line.count("|") >= 3

_PLACEHOLDER = re.compile(
    r'^<<<PLACEHOLDER\|(fig|tbl)\|([^|]+)\|desc="(.*?)">>>\s*$'
)


def _slug(s: str) -> str:
    s = s.strip()
    s = re.sub(r'\s+', '-', s)
    s = re.sub(r'[^0-9A-Za-z가-힣\-]+', '', s)
    s = re.sub(r'-{2,}', '-', s).strip('-')
    return s.lower()


class Md(BaseChunkingStrategy):
    """
    Markdown 구조를 보존하며 토큰 기반 soft/hard 한도를 지키는 청킹 전략.
    - 섹션 경계를 우선 고려
    - 표/코드/수식/PLACEHOLDER 같은 원자 블록은 가능하면 단독 청크
    - hard 초과 시 안전 분할 수행
    - 청크 간 전역 overlap 적용(내부 분할로 생성된 이웃은 제외)
    """

    def __init__(self, parameters: Dict[Any, Any] = None):
        super().__init__(parameters)
        if AutoTokenizer is None:
            raise ImportError("transformers is required for Markdown chunking. Install it with: pip install transformers")

        model_name = self.parameters.get("model_name", "klue/bert-base")
        self.soft = int(self.parameters.get("soft_target", 350))
        self.hard = int(self.parameters.get("hard_limit", 520))
        self.overlap = int(self.parameters.get("overlap", 60))
        self.start_new_on_heading = bool(self.parameters.get("start_new_on_heading", True))
        self.materialize_assets = bool(self.parameters.get("materialize_assets", True))

        if not (self.overlap < self.soft < self.hard):
            raise ValueError("Require: overlap < soft_target < hard_limit")

        logger.info(f"[Markdown] Loading tokenizer model: {model_name}, soft={self.soft}, hard={self.hard}, overlap={self.overlap}")
        self.tok = AutoTokenizer.from_pretrained(model_name, use_fast=True)
        try:
            self.tok.model_max_length = 10**9
        except Exception:
            pass

    # ------------------------ 유틸 ------------------------
    def _len_tokens(self, s: str) -> int:
        return len(self.tok.encode(s, add_special_tokens=False, truncation=False))

    def _split_block_by_tokens(self, text: str) -> List[str]:
        ids = self.tok.encode(text, add_special_tokens=False, truncation=False)
        out: List[str] = []
        i = 0
        while i < len(ids):
            j = min(i + self.hard, len(ids))
            out.append(self.tok.decode(ids[i:j], skip_special_tokens=True, clean_up_tokenization_spaces=True).strip())
            i = max(j - self.overlap, i + 1)
        return [s for s in out if s]

    def _split_para_by_sentence_guarded(self, text: str) -> List[str]:
        sentences = re.split(r'(?<=[\.?!])\s+', text.strip())
        pieces: List[str] = []
        cur = ""
        for s in sentences:
            s = s.strip()
            if not s:
                continue
            if self._len_tokens(s) > self.hard:
                if cur.strip():
                    pieces.append(cur.strip()); cur = ""
                pieces.extend(self._split_block_by_tokens(s))
                continue
            cand = (cur + (" " if cur else "") + s)
            if self._len_tokens(cand) <= self.hard:
                cur = cand
            else:
                if cur.strip():
                    pieces.append(cur.strip())
                cur = s
        if cur.strip():
            pieces.append(cur.strip())
        return pieces

    def _split_table_block_by_rows(self, text: str) -> List[str]:
        rows = [r for r in text.splitlines() if r.strip()]
        header_rows: List[str] = []
        if len(rows) >= 2 and re.match(r'^\s*\|', rows[0]) and re.match(r'^\s*\|\s*[-:\s|]+\|\s*$', rows[1]):
            header_rows = rows[:2]

        parts: List[str] = []
        cur = ""
        first_piece = True

        def flush(with_header: bool):
            nonlocal cur
            if cur.strip():
                if with_header and header_rows:
                    body = cur.strip().splitlines()
                    cur = "\n".join(header_rows + body)
                parts.append(cur.strip())
                cur = ""

        for r in rows:
            cand = (cur + ("\n" if cur else "") + r)
            if self._len_tokens(cand) <= self.hard:
                cur = cand
            else:
                flush(with_header=not first_piece)
                first_piece = False
                cur = r
        flush(with_header=not first_piece)
        return parts

    def _materialize_asset_text(self, kind: str, uid: str, desc: str) -> str:
        label = "그림" if kind == "fig" else "표"
        return f"【{label}: {uid}】 {desc}".strip()

    # --------------------- 파서: MD → 블록 ---------------------
    def _parse_blocks(self, text: str) -> List[Dict[str, Any]]:
        blocks: List[Dict[str, Any]] = []
        lines = text.splitlines()
        i, n = 0, len(lines)
        section_path_stack: List[Tuple[int, str]] = []

        def cur_section_path() -> List[str]:
            return [t for _, t in section_path_stack]

        def cur_anchor() -> Optional[str]:
            slugs = [_slug(t) for t in cur_section_path() if _slug(t)]
            return "/".join(slugs) if slugs else None

        def push_block(kind: str, start_i: int, end_i: int, payload: Optional[Dict[str, Any]] = None):
            blk_text = "\n".join(lines[start_i:end_i])
            data: Dict[str, Any] = {
                "kind": kind,
                "text": blk_text,
                "start": start_i,
                "end": end_i,
                "section_path": cur_section_path(),
                "anchor": cur_anchor(),
            }
            if payload:
                data.update(payload)
            blocks.append(data)

        last_i = -1
        while i < n:
            if i == last_i:
                i += 1
                continue
            last_i = i

            line = lines[i]

            m = _HEADING.match(line)
            if m:
                level = len(m.group(1))
                title = m.group(2).strip()
                section_path_stack = [(l, t) for (l, t) in section_path_stack if l < level]
                section_path_stack.append((level, title))
                push_block("heading", i, i + 1, {"level": level, "title": title})
                i += 1
                continue

            pm = _PLACEHOLDER.match(line)
            if pm:
                payload = {"asset": {"kind": pm.group(1), "uid": pm.group(2), "desc": pm.group(3)}}
                push_block("asset", i, i + 1, payload)
                i += 1
                continue

            if _CODEFENCE.match(line):
                j = i + 1
                while j < n and not _CODEFENCE.match(lines[j]):
                    j += 1
                j = min(j + 1, n)
                push_block("code", i, j)
                i = j
                continue

            if _MATH_FENCE.match(line):
                j = i + 1
                while j < n and not _MATH_FENCE.match(lines[j]):
                    j += 1
                j = min(j + 1, n)
                push_block("math", i, j)
                i = j
                continue

            if _is_table_line(line):
                j = i + 1
                while j < n and _is_table_line(lines[j]):
                    j += 1
                push_block("table", i, j)
                i = j
                continue

            j = i + 1
            while j < n and lines[j].strip() != "":
                if (
                    _HEADING.match(lines[j]) or
                    _CODEFENCE.match(lines[j]) or
                    _MATH_FENCE.match(lines[j]) or
                    _PLACEHOLDER.match(lines[j]) or
                    _is_table_line(lines[j])
                ):
                    break
                j += 1

            push_block("para", i, j)
            while j < n and lines[j].strip() == "":
                j += 1
            i = j

        return blocks

    # ---------------------- 퍼블릭 API ----------------------
    def _download_text(self, bucket: str, path: str, request_headers: Dict[str, Any] | None) -> str:
        presign_url = "http://hebees-python-backend:8000/api/v1/files/presigned"
        params = {"bucket": bucket, "path": path, "inline": "false"}
        with httpx.Client(timeout=3600.0) as client:
            r = client.get(presign_url, params=params, headers={k: v for k, v in (request_headers or {}).items() if v})
            r.raise_for_status()
            try:
                js = r.json()
                url = js.get("result", {}).get("data", {}).get("url")
            except Exception:
                url = r.text.strip().strip('"')
            if not url:
                raise RuntimeError("Failed to resolve presigned URL for chunking")
            rd = client.get(url)
            rd.raise_for_status()
            return rd.text

    def chunk(self, bucket: str, path: str, request_headers: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
        # 원격에서 마크다운 다운로드
        raw_text = self._download_text(bucket, path, request_headers) or ""
        if not raw_text.strip():
            return []

        # 0) 페이지 병합 준비 (단일 페이지)
        page_of_line: List[int] = []
        norm_pages: List[Dict[str, Any]] = []
        page_no = 1
        lines = raw_text.splitlines()
        out_lines: List[str] = []
        for ln in lines:
            if _PLACEHOLDER.match(ln):
                out_lines.append(ln)
                continue
            out_lines.append(ln)
        t = "\n".join(out_lines)
        norm_pages.append({"page": page_no, "text": t})
        line_count = max(1, len(t.splitlines()))
        page_of_line.extend([page_no] * line_count)

        merged_text = "\n".join(np["text"] for np in norm_pages)
        blocks = self._parse_blocks(merged_text)

        chunks: List[Dict[str, Any]] = []
        cur_blocks: List[Dict[str, Any]] = []
        cur_txt = ""
        chunk_idx = 0

        def next_id() -> int:
            nonlocal chunk_idx
            cid = chunk_idx
            chunk_idx += 1
            return cid

        line_cursor = 0

        def _stamp_block_page_and_advance(b: Dict[str, Any]) -> None:
            nonlocal line_cursor
            if not page_of_line:
                b["_page"] = norm_pages[0]["page"]
                return
            idx = min(line_cursor, len(page_of_line) - 1)
            b["_page"] = page_of_line[idx]
            consumed = max(1, len(b.get("text", "").splitlines()))
            line_cursor += consumed

        def _page_of_cur_blocks(default_page: int) -> int:
            if not cur_blocks:
                return default_page
            return min(b.get("_page", default_page) for b in cur_blocks)

        def _flush_chunk():
            nonlocal cur_blocks, cur_txt
            if not cur_txt.strip():
                cur_blocks, cur_txt = [], ""
                return

            # 가장 최근 섹션 경로
            section_path: List[str] = []
            for b in reversed(cur_blocks):
                if b.get("section_path"):
                    section_path = b["section_path"]
                    break

            # 자산/블록타입 수집
            block_types: List[str] = []
            assets: List[Dict[str, Any]] = []
            for b in cur_blocks:
                block_types.append(b["kind"])
                if b.get("asset"):
                    assets.append(b["asset"])

            rep_page = _page_of_cur_blocks(default_page=norm_pages[0]["page"])
            chunks.append({
                "page": rep_page,
                "chunk_id": next_id(),
                "text": cur_txt.strip(),
                "section_path": section_path,
                "anchor": "/".join([_slug(x) for x in section_path if _slug(x)]) or None,
                "block_types": block_types,
                "assets": assets,
            })
            cur_blocks, cur_txt = [], ""

        # 3) 블록 순회
        for b in blocks:
            _stamp_block_page_and_advance(b)

            if self.start_new_on_heading and b["kind"] == "heading" and cur_txt:
                _flush_chunk()

            b_text = b["text"]
            if self.materialize_assets and b.get("asset"):
                a = b["asset"]
                b_text = self._materialize_asset_text(a.get("kind"), a.get("uid"), a.get("desc"))

            candidate = (cur_txt + ("\n\n" if cur_txt else "") + b_text)
            cand_len = self._len_tokens(candidate)

            if cand_len > self.soft and cur_txt:
                _flush_chunk()
                candidate = b_text
                cand_len = self._len_tokens(candidate)

            if cand_len <= self.hard:
                cur_blocks.append(b)
                cur_txt = candidate
                continue

            # 하드 초과 → 분해
            _flush_chunk()
            if b["kind"] == "para":
                for piece in self._split_para_by_sentence_guarded(b_text):
                    chunks.append({
                        "page": b["_page"],
                        "chunk_id": next_id(),
                        "text": piece,
                        "section_path": b["section_path"],
                        "anchor": b["anchor"],
                        "block_types": [b["kind"]],
                        "assets": [],
                    })
                continue
            if b["kind"] == "table":
                for piece in self._split_table_block_by_rows(b_text):
                    chunks.append({
                        "page": b["_page"],
                        "chunk_id": next_id(),
                        "text": piece,
                        "section_path": b["section_path"],
                        "anchor": b["anchor"],
                        "block_types": [b["kind"]],
                        "assets": [],
                    })
                continue
            for piece in self._split_block_by_tokens(b_text):
                chunks.append({
                    "page": b["_page"],
                    "chunk_id": next_id(),
                    "text": piece,
                    "section_path": b["section_path"],
                    "anchor": b["anchor"],
                    "block_types": [b["kind"]],
                    "assets": [b["asset"]] if b.get("asset") else [],
                })

        if cur_txt:
            _flush_chunk()

        # 4) 전역 오버랩 (내부 분해 생성 이웃은 제외)
        if self.overlap > 0 and len(chunks) > 1:
            def tail_tokens(s: str, n: int) -> str:
                ids = self.tok.encode(s, add_special_tokens=False, truncation=False)
                tail = ids[-n:]
                return self.tok.decode(tail, skip_special_tokens=True, clean_up_tokenization_spaces=True).strip()

            originals = [c["text"] for c in chunks]
            SPLIT_ORIGINS = {"table-rows", "para-sent", "token-window"}
            # 본 구현에서는 _origin 키를 노출하지 않으므로, 외부 분해 이웃 판정은 생략
            for i in range(1, len(chunks)):
                tail = tail_tokens(originals[i - 1], self.overlap)
                if tail:
                    chunks[i]["text"] = (tail + "\n\n" + chunks[i]["text"]).strip()

        return chunks


