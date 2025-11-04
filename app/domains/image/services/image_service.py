"""
이미지 생성 서비스
Google NanoBanana를 사용하여 이미지를 생성하고 MinIO에 업로드한 후 DB에 저장
"""
import logging
import uuid
import hashlib
from datetime import datetime
from typing import List, Optional
from PIL import Image
from io import BytesIO
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.settings import settings
from app.domains.file.models.file import File
from app.domains.user.models.user import User
from app.domains.file.repositories.file_repository import FileRepository
from app.domains.offer.repositories.offer_repository import OfferRepository
from app.domains.file.repositories.file_category_repository import FileCategoryRepository
from app.domains.user.repositories.user_repository import UserRepository
from ..schemas.image_request import ImageGenerateRequest
from ..schemas.image_regenerate_request import ImageRegenerateRequest
from ..schemas.image_response import ImageResponse
from .minio_service import MinIOService
from .gemini_client import GeminiClient

logger = logging.getLogger(__name__)


class ImageService:
    def __init__(self, minio_service: MinIOService):
        self.minio_service = minio_service
        self.gemini_client = GeminiClient()
    
    async def get_user_by_uuid(
        self,
        user_uuid: str,
        db: AsyncSession
    ) -> User:
        if not user_uuid:
            raise ValueError("x-user-uuid 헤더가 필요합니다.")
        
        try:
            user_no = bytes.fromhex(user_uuid.replace("-", ""))
        except ValueError:
            raise ValueError("유효하지 않은 사용자 UUID 형식입니다.")
        
        user = await UserRepository.find_by_user_no(db, user_no)
        if not user:
            raise ValueError("사용자를 찾을 수 없습니다.")
        
        if user.deleted_at:
            raise ValueError("삭제된 사용자입니다.")
        
        return user
    
    async def generate_image(
        self,
        request: ImageGenerateRequest,
        user_uuid: str,
        db: AsyncSession
    ) -> List[ImageResponse]:
        user = await self.get_user_by_uuid(user_uuid, db)
        
        offer = await OfferRepository.find_by_offer_no(db, user.offer_no)
        if not offer:
            raise ValueError(f"OFFER 테이블에 OFFER_NO '{user.offer_no}'가 존재하지 않습니다.")
        
        file_category = await FileCategoryRepository.find_by_name(db, "이미지")
        if not file_category:
            raise ValueError("FILE_CATEGORY 테이블에 NAME이 '이미지'인 레코드가 없습니다. 먼저 생성해주세요.")
        
        file_category_no = file_category.file_category_no
        
        # Google Gemini API를 통해 이미지 생성
        generated_image = await self.gemini_client.generate_image(
            prompt=request.prompt,
            size=request.size,
            style=request.style
        )
        
        # 이미지 파일명 및 경로 생성
        file_uuid = uuid.uuid4()
        file_name = f"{file_uuid.hex}.png"
        user_uuid_clean = user_uuid.replace("-", "")
        minio_path = f"{settings.minio_image_storage_base_path}/{user_uuid_clean}/{file_name}"
        
        user_no = user.user_no
        
        # 파일 해시 계산
        image_byte_stream = BytesIO()
        generated_image.save(image_byte_stream, format="PNG")
        image_bytes = image_byte_stream.getvalue()
        file_hash = hashlib.sha256(image_bytes).hexdigest()
        file_size = len(image_bytes)
        
        # MinIO에 업로드
        self.minio_service.upload_image(
            image=generated_image,
            object_name=minio_path,
            content_type="image/png"
        )
        
        # 이미지 URL 생성
        image_url = self.minio_service.get_image_url(minio_path)
        
        # DB에 메타데이터 저장
        file_record = File(
            file_no=file_uuid.bytes,
            user_no=user_no,
            name=file_name,
            size=file_size,
            type="png",
            hash=file_hash,
            description=f"Generated image from prompt: {request.prompt[:100]}",
            bucket=self.minio_service.bucket_name,
            path=minio_path,
            file_category_no=file_category_no,
            offer_no=offer.offer_no,
            collection_no=None,
            source_no=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Repository를 통해 저장
        await FileRepository.save(db, file_record)
        
        # 응답 스키마 생성
        image_response = ImageResponse(
            image_id=file_uuid.hex,
            url=image_url,
            type="png"
        )
        
        logger.info(f"이미지 생성 및 저장 완료: {file_uuid.hex}")
        
        return [image_response]
    
    def _extract_prompt_from_description(self, description: str) -> str:
        """description에서 프롬프트 추출"""
        prefix = "Generated image from prompt: "
        if description.startswith(prefix):
            return description[len(prefix):].strip()
        return description.strip()
    
    async def regenerate_image(
        self,
        request: ImageRegenerateRequest,
        user_uuid: str,
        db: AsyncSession
    ) -> List[ImageResponse]:
        user = await self.get_user_by_uuid(user_uuid, db)
        
        try:
            image_id_hex = request.image_id.replace("-", "")
            original_file_no = bytes.fromhex(image_id_hex)
        except ValueError as e:
            raise ValueError(f"유효하지 않은 이미지 ID 형식입니다: {request.image_id}")
        
        original_file = await FileRepository.find_by_file_no(db, original_file_no)
        
        if not original_file:
            raise ValueError("원본 이미지를 찾을 수 없습니다.")
        
        if original_file.user_no != user.user_no:
            raise ValueError("다른 사용자의 이미지는 재생성할 수 없습니다.")
        
        offer = await OfferRepository.find_by_offer_no(db, user.offer_no)
        if not offer:
            raise ValueError(f"OFFER 테이블에 OFFER_NO '{user.offer_no}'가 존재하지 않습니다.")
        
        file_category = await FileCategoryRepository.find_by_name(db, "이미지")
        if not file_category:
            raise ValueError("FILE_CATEGORY 테이블에 NAME이 '이미지'인 레코드가 없습니다. 먼저 생성해주세요.")
        
        file_category_no = file_category.file_category_no
        
        original_prompt = self._extract_prompt_from_description(original_file.description)
        prompt = request.prompt if request.prompt else original_prompt
        size = request.size if request.size else "1024x1024"
        style = request.style if request.style is not None else None
        
        generated_image = await self.gemini_client.generate_image(
            prompt=prompt,
            size=size,
            style=style
        )
        
        image_byte_stream = BytesIO()
        generated_image.save(image_byte_stream, format="PNG")
        image_bytes = image_byte_stream.getvalue()
        file_hash = hashlib.sha256(image_bytes).hexdigest()
        file_size = len(image_bytes)
        
        minio_path = original_file.path
        
        self.minio_service.upload_image(
            image=generated_image,
            object_name=minio_path,
            content_type="image/png"
        )
        
        # 캐시 무효화를 위해 타임스탬프가 포함된 URL 생성
        image_url = self.minio_service.get_image_url(minio_path, cache_bust=True)
        
        # 기존 FILE 엔티티 업데이트
        original_file.size = file_size
        original_file.hash = file_hash
        original_file.description = f"Generated image from prompt: {prompt[:100]}"
        original_file.updated_at = datetime.utcnow()
        
        merged_file = await db.merge(original_file)
        await db.commit()
        await db.refresh(merged_file)
        
        image_response = ImageResponse(
            image_id=original_file.file_no.hex(),
            url=image_url,
            type=original_file.type
        )
        
        logger.info(f"이미지 재생성 및 업데이트 완료: {request.image_id}")
        
        return [image_response]
    
    async def get_image_by_id(
        self,
        image_id: str,
        db: AsyncSession
    ) -> Optional[ImageResponse]:
        try:
            file_no = bytes.fromhex(image_id)
            file_record = await FileRepository.find_by_file_no(db, file_no)
            
            if not file_record:
                return None
            
            # MinIO URL 생성
            image_url = self.minio_service.get_image_url(
                file_record.path,
                cache_bust=True
            )
            
            return ImageResponse(
                image_id=file_record.file_no.hex(),
                url=image_url,
                type=file_record.type
            )
            
        except Exception as e:
            logger.error(f"이미지 조회 실패: {e}", exc_info=True)
            return None
    
    async def get_images_by_user_uuid(
        self,
        user_uuid: str,
        db: AsyncSession,
        limit: Optional[int] = 20,
        offset: Optional[int] = 0
    ) -> List[ImageResponse]:
        user = await self.get_user_by_uuid(user_uuid, db)
        
        file_category = await FileCategoryRepository.find_by_name(db, "이미지")
        if not file_category:
            raise ValueError("FILE_CATEGORY 테이블에 NAME이 '이미지'인 레코드가 없습니다. 먼저 생성해주세요.")
        
        file_records = await FileRepository.find_by_user_no_and_category(
            db=db,
            user_no=user.user_no,
            file_category_no=file_category.file_category_no,
            limit=limit,
            offset=offset
        )
        
        image_responses = []
        for file_record in file_records:
            # updated_at을 기반으로 캐시 무효화
            image_url = self.minio_service.get_image_url(
                file_record.path,
                cache_bust=True
            )
            image_response = ImageResponse(
                image_id=file_record.file_no.hex(),
                url=image_url,
                type=file_record.type
            )
            image_responses.append(image_response)
        
        return image_responses
    
    async def delete_image(
        self,
        image_id: str,
        user_uuid: str,
        db: AsyncSession
    ) -> bool:
        user = await self.get_user_by_uuid(user_uuid, db)
        
        try:
            image_id_hex = image_id.replace("-", "")
            file_no = bytes.fromhex(image_id_hex)
        except ValueError as e:
            raise ValueError(f"유효하지 않은 이미지 ID 형식입니다: {image_id}")
        
        file_record = await FileRepository.find_by_file_no(db, file_no)
        
        if not file_record:
            raise ValueError("이미지를 찾을 수 없습니다.")
        
        if file_record.user_no != user.user_no:
            raise ValueError("다른 사용자의 이미지는 삭제할 수 없습니다.")
        
        minio_path = file_record.path
        
        success = self.minio_service.delete_image(minio_path)
        if not success:
            logger.warning(f"MinIO에서 이미지 삭제 실패: {minio_path}, 하지만 DB 레코드는 삭제합니다.")
        
        await FileRepository.delete(db, file_record)
        
        logger.info(f"이미지 삭제 완료: {image_id}")
        
        return True
