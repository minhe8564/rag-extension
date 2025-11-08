"""
MinIO 저장소 서비스
이미지 파일을 MinIO에 업로드하고 관리
"""
from minio import Minio
from minio.error import S3Error
from io import BytesIO
from typing import Optional
from PIL import Image
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from datetime import datetime
import logging
from app.core.config.settings import settings

logger = logging.getLogger(__name__)

class MinIOService:
    def __init__(self):
        """MinIO 클라이언트 초기화"""
        self.client = None
        self.bucket_name = settings.minio_image_bucket_name
        self._initialized = False
    
    def _initialize_client(self):
        """MinIO 클라이언트를 지연 초기화"""
        if self.client is None:
            self.client = Minio(
                endpoint=settings.minio_endpoint,
                access_key=settings.minio_access_key,
                secret_key=settings.minio_secret_key,
                secure=settings.minio_use_ssl,
                region=settings.minio_region if settings.minio_region else None
            )
    
    def _lazy_ensure_bucket_exists(self):
        """버킷이 존재하는지 확인하고 없으면 생성"""
        if not self._initialized:
            self._initialize_client()
            try:
                self._ensure_bucket_exists()
                self._initialized = True
            except Exception as e:
                logger.warning(f"MinIO 버킷 확인 실패 (나중에 재시도): {e}")
                self._initialized = False

    def _ensure_bucket_exists(self):
        """버킷이 존재하는지 확인하고 없으면 생성, 공개 읽기 정책 설정"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"버킷 '{self.bucket_name}' 생성 완료")
            
            # 버킷 정책 설정: 공개 읽기 접근 허용
            self._set_bucket_policy()
            logger.debug(f"버킷 '{self.bucket_name}' 정책 설정 완료")
        except S3Error as e:
            logger.error(f"버킷 확인/생성 실패: {e}")
            raise
    
    def _set_bucket_policy(self):
        """버킷 공개 읽기 정책 설정"""
        import json
        
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": ["*"]},
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{self.bucket_name}/*"]
                }
            ]
        }
        
        try:
            policy_json = json.dumps(policy)
            
            try:
                if hasattr(self.client, 'set_bucket_policy'):
                    self.client.set_bucket_policy(self.bucket_name, policy_json)
                    logger.info(f"버킷 '{self.bucket_name}' 공개 읽기 정책 설정 완료")
                else:
                    logger.warning(f"set_bucket_policy 메서드를 사용할 수 없습니다. MinIO 관리 콘솔에서 수동으로 정책을 설정해주세요.")
                    logger.warning(f"정책 JSON:\n{policy_json}")
            except S3Error as e:
                logger.warning(f"버킷 정책 설정 실패: {e}. MinIO 관리 콘솔에서 수동 설정이 필요할 수 있습니다.")
                logger.warning(f"정책 JSON:\n{policy_json}")
        except Exception as e:
            logger.warning(f"버킷 정책 설정 중 오류 발생: {e}. MinIO 관리 콘솔에서 수동 설정이 필요할 수 있습니다.")
            logger.warning(f"정책 JSON:\n{json.dumps(policy, indent=2)}")

    def upload_image(
        self,
        image: Image.Image,
        object_name: str,
        content_type: str = "image/png"
    ) -> str:
        """
        이미지를 MinIO에 업로드
        """
        self._lazy_ensure_bucket_exists()
        try:
            image_bytes = BytesIO()
            if content_type == "image/png":
                image.save(image_bytes, format="PNG")
            elif content_type == "image/jpeg" or content_type == "image/jpg":
                image.save(image_bytes, format="JPEG")
            else:
                # 기본값 PNG
                image.save(image_bytes, format="PNG")
                content_type = "image/png"
            
            image_bytes.seek(0)
            file_size = len(image_bytes.getvalue())

            # MinIO에 업로드
            self.client.put_object(
                bucket_name = self.bucket_name,
                object_name = object_name,
                data = image_bytes,
                length = file_size,
                content_type = content_type
            )

            logger.info(f"이미지 업로드 완료: {object_name} ({file_size} bytes)")
            return object_name
        except S3Error as e:
            logger.error(f"이미지 업로드 실패: {e}")
            raise e

    def upload_image_from_bytes(
        self,
        image_bytes: bytes,
        object_name: str,
        content_type: str = "image/png"
    ) -> str:
        """
        바이트 데이터를 MinIO에 업로드
        """
        self._lazy_ensure_bucket_exists()
        try:
            data_stream = BytesIO(image_bytes)
            
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=data_stream,
                length=len(image_bytes),
                content_type=content_type
            )
            
            logger.info(f"이미지 업로드 완료: {object_name} ({len(image_bytes)} bytes)")
            return object_name
            
        except S3Error as e:
            logger.error(f"이미지 업로드 실패: {e}")
            raise
    
    def _add_cache_bust_param(self, url: str) -> str:
        
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        query_params['v'] = [str(int(datetime.utcnow().timestamp()))]
        new_query = urlencode(query_params, doseq=True)
        
        return urlunparse((
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            parsed_url.params,
            new_query,
            parsed_url.fragment
        ))
    
    def get_image_url(self, object_name: str, expires_seconds: int = 3600 * 24 * 7, use_presigned: Optional[bool] = None, cache_bust: bool = False) -> str:
        """
        이미지 접근 URL 생성 (공개 URL 사용)
        """
        public_base_url = settings.minio_public_endpoint_url
    
        if use_presigned is None:
            use_presigned = settings.minio_use_presigned_url
        
        if use_presigned:
            self._lazy_ensure_bucket_exists()
            try:
                from datetime import timedelta
                presigned_url = self.client.presigned_get_object(
                    bucket_name=self.bucket_name,
                    object_name=object_name,
                    expires=timedelta(seconds=expires_seconds)
                )
                
                if public_base_url != settings.minio_endpoint_url:
                    from urllib.parse import urlparse, urlunparse
                    parsed = urlparse(presigned_url)
                    public_parsed = urlparse(public_base_url)
                    new_url = urlunparse((
                        public_parsed.scheme,
                        public_parsed.netloc,
                        parsed.path,
                        parsed.params,
                        parsed.query,
                        parsed.fragment
                    ))
                    base_url = new_url
                else:
                    base_url = presigned_url
                
                # 캐시 무효화를 위한 타임스탬프 추가
                if cache_bust:
                    base_url = self._add_cache_bust_param(base_url)
                
                return base_url
            except Exception as e:
                logger.warning(f"Presigned URL 생성 실패, 공개 URL 사용: {e}")
        
        # 경로 조합 시 슬래시 중복 방지
        object_name = object_name.lstrip("/")
        public_base_url = public_base_url.rstrip("/")
        
        # object_name에서 "images/" prefix 제거하고 /image 경로 추가
        if object_name.startswith("images/"):
            object_name = object_name[len("images/"):]
        
        base_url = f"{public_base_url}/image/{object_name}"
        
        # 캐시 무효화를 위한 타임스탬프 추가
        if cache_bust:
            base_url = self._add_cache_bust_param(base_url)
        
        return base_url
    
    def delete_image(self, object_name: str) -> bool:
        """
        이미지 삭제
        """
        self._lazy_ensure_bucket_exists()
        try:
            self.client.remove_object(
                bucket_name=self.bucket_name,
                object_name=object_name
            )
            logger.info(f"이미지 삭제 완료: {object_name}")
            return True
        except S3Error as e:
            logger.error(f"이미지 삭제 실패: {e}")
            return False
    
    def image_exists(self, object_name: str) -> bool:
        """
        이미지 존재 여부 확인
        """
        self._lazy_ensure_bucket_exists()
        try:
            self.client.stat_object(
                bucket_name=self.bucket_name,
                object_name=object_name
            )
            return True
        except S3Error:
            return False
