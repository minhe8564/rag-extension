"""
Google Gemini API 클라이언트
이미지 생성 로직을 별도 모듈로 분리
"""
import base64
import asyncio
import logging
import math
from typing import Optional
from PIL import Image
from io import BytesIO
from google import genai
from google.genai import types

from app.core.config.settings import settings

logger = logging.getLogger(__name__)


class GeminiClient:
    def __init__(self):
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model_name = settings.gemini_image_model_name
    
    def _parse_size_to_aspect_ratio(self, size: str) -> Optional[str]:
        if ":" in size:
            return size
        try:
            if "x" in size:
                width, height = map(int, size.split("x"))
                gcd = math.gcd(width, height)
                ratio_w = width // gcd
                ratio_h = height // gcd
                return f"{ratio_w}:{ratio_h}"
        except (ValueError, AttributeError):
            pass
        
        # 변환 실패 시 None 반환
        return None
    
    def _prepare_prompt(
        self,
        prompt: str,
        size: str = "1024x1024",
        style: Optional[str] = None
    ) -> str:
        # 프롬프트 시작 단어 확인
        if not prompt.lower().startswith(("create", "generate", "make", "draw", "design")):
            full_prompt = f"Create a picture of {prompt}"
        else:
            full_prompt = prompt
        
        # 텍스트 없이 생성하도록 명시
        if "no text" not in full_prompt.lower() and "without text" not in full_prompt.lower() and "텍스트 없이" not in full_prompt:
            full_prompt = f"{full_prompt}, without any text or words"
        
        # 스타일 추가
        if style:
            full_prompt = f"{full_prompt}, style: {style}"
        
        # Aspect ratio 추가
        aspect_ratio = self._parse_size_to_aspect_ratio(size)
        if aspect_ratio:
            full_prompt = f"{full_prompt}, aspect ratio {aspect_ratio}"
        
        return full_prompt
    
    def _create_gemini_content(self, prompt: str) -> list:
        if hasattr(types.Part, 'from_text'):
            try:
                part_obj = types.Part.from_text(text=prompt)
                return [
                    types.Content(
                        role="user",
                        parts=[part_obj],
                    ),
                ]
            except Exception as e:
                logger.debug("types.Part.from_text() 실패, 다음 전략 시도: %s", e)
        try:
            part_obj = types.Part(text=prompt)
            return [
                types.Content(
                    role="user",
                    parts=[part_obj],
                ),
            ]
        except Exception as e:
            logger.debug("types.Part(text=...) 실패, 문자열 프롬프트로 fallback: %s", e)
        
        logger.warning("Gemini types 모듈 사용 불가, 문자열 프롬프트 사용")
        return [prompt]
    
    def _create_gemini_config(self) -> Optional[object]:
        try:
            return types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                candidate_count=1,
            )
        except (AttributeError, TypeError) as e:
            logger.debug("GenerateContentConfig 사용 불가: %s", e)
            return None
    
    def _call_gemini_api(
        self,
        contents: list,
        config: Optional[object] = None
    ):
        try:
            if config is not None:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=contents,
                    config=config,
                )
            else:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=contents,
                )
            logger.debug("Gemini API 호출 성공")
            return response
        except Exception as e:
            logger.error("Gemini API 호출 실패: %s", e, exc_info=True)
            raise
    
    def _extract_image_from_response(self, response) -> Image.Image:
        if not getattr(response, "candidates", None):
            raise ValueError("응답에 candidates가 없습니다.")
        
        first_candidate = response.candidates[0]
        if not getattr(first_candidate, "content", None):
            raise ValueError("응답에 content가 없습니다.")
        
        parts = getattr(first_candidate.content, "parts", None)
        if not parts:
            raise ValueError("응답에서 이미지 데이터를 찾지 못했습니다.")
        
        # 이미지 데이터 추출
        image_bytes = None
        mime_type = "image/png"
        
        for part in parts:
            try:
                inline_data = getattr(part, "inline_data", None)
                if inline_data and getattr(inline_data, "data", None):
                    raw_data = inline_data.data
                    
                    # Base64 디코딩 또는 바이트 처리
                    if isinstance(raw_data, str):
                        try:
                            image_bytes = base64.b64decode(raw_data)
                        except Exception as e:
                            logger.debug("Base64 디코딩 실패: %s", e)
                            continue
                    else:
                        image_bytes = raw_data
                    
                    mime_attr = getattr(inline_data, "mime_type", None)
                    if mime_attr:
                        mime_type = mime_attr
                    
                    break
                
                text_attr = getattr(part, "text", None)
                if text_attr:
                    logger.warning("Gemini가 텍스트를 반환했습니다: %s", text_attr)
                    
            except AttributeError as e:
                logger.debug("Part 속성 접근 오류: %s", e)
                continue
        
        if not image_bytes:
            raise ValueError(
                "응답에서 이미지 데이터를 찾지 못했습니다. "
                "Gemini가 이미지를 생성하지 않았을 수 있습니다."
            )
        
        # PIL Image 객체로 변환
        image = Image.open(BytesIO(image_bytes))
        if image.mode != "RGB":
            image = image.convert("RGB")
        
        return image
    
    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        style: Optional[str] = None
    ) -> Image.Image:
        try:
            full_prompt = self._prepare_prompt(prompt, size, style)

            def _generate_sync():
                contents = self._create_gemini_content(full_prompt)
                config = self._create_gemini_config()
                response = self._call_gemini_api(contents, config)

                return self._extract_image_from_response(response)
            
            loop = asyncio.get_event_loop()
            image = await loop.run_in_executor(None, _generate_sync)
            
            logger.info("Gemini API 이미지 생성 완료: %s", full_prompt)
            return image
            
        except Exception as e:
            logger.error("Gemini API 호출 실패: %s", e, exc_info=True)
            raise Exception(f"이미지 생성에 실패했습니다: {str(e)}")
