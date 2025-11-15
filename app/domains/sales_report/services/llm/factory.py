"""LLM Provider Factory - LLM 프로바이더 생성 팩토리"""
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.domains.sales_report.services.llm.base import BaseLLMProvider
from app.domains.sales_report.services.llm.qwen_provider import QwenLLMProvider
from app.domains.sales_report.services.llm.gpt_provider import GPTLLMProvider
from app.domains.runpod.repositories.runpod_repository import RunpodRepository
from app.domains.sales_report.exceptions import RunpodNotFoundError

logger = logging.getLogger(__name__)


class LLMProviderFactory:
    """
    LLM 프로바이더 팩토리

    Qwen/GPT 등 다양한 LLM 프로바이더 인스턴스를 생성하는 팩토리 클래스입니다.
    새로운 프로바이더 추가 시 이 클래스만 수정하면 됩니다.

    Example:
        # 환경 설정에 따라 자동 선택
        llm = await LLMProviderFactory.create(db)

        # 명시적 프로바이더 선택
        llm = await LLMProviderFactory.create(db, provider_name="gpt")
    """

    @staticmethod
    async def create(
        db: Optional[AsyncSession] = None,
        provider_name: Optional[str] = None
    ) -> tuple[BaseLLMProvider, str]:
        """
        LLM 프로바이더 인스턴스 생성

        Args:
            db: 데이터베이스 세션 (Qwen 사용 시 Runpod 조회에 필요)
            provider_name: 프로바이더 이름 (None이면 settings.llm_provider 사용)

        Returns:
            Tuple[BaseLLMProvider, str]: (프로바이더 인스턴스, 모델명)

        Raises:
            ValueError: 지원하지 않는 프로바이더이거나 필수 설정이 누락된 경우
            RunpodNotFoundError: Qwen 사용 시 Runpod 서버를 찾을 수 없는 경우
        """
        provider = provider_name or settings.llm_provider

        if provider == "qwen":
            return await LLMProviderFactory._create_qwen_provider(db)
        elif provider == "gpt":
            return LLMProviderFactory._create_gpt_provider()
        else:
            available_providers = "qwen, gpt"
            raise ValueError(
                f"지원하지 않는 LLM 프로바이더: {provider}. "
                f"사용 가능한 프로바이더: {available_providers}"
            )

    @staticmethod
    async def _create_qwen_provider(db: Optional[AsyncSession]) -> tuple[QwenLLMProvider, str]:
        """
        Qwen LLM 프로바이더 생성 (Runpod 기반)

        Args:
            db: 데이터베이스 세션 (Runpod 조회에 필요)

        Returns:
            Tuple[QwenLLMProvider, str]: (Qwen 프로바이더, 모델명)

        Raises:
            ValueError: DB 세션이 없는 경우
            RunpodNotFoundError: Runpod 서버를 찾을 수 없는 경우
        """
        if not db:
            raise ValueError("Qwen 프로바이더 생성에는 데이터베이스 세션이 필요합니다.")

        # Runpod에서 Qwen 서버 주소 조회
        runpod = await RunpodRepository.find_by_name(db, "qwen3")

        if not runpod or not runpod.address:
            logger.warning("Qwen 서버를 찾을 수 없습니다.")
            raise RunpodNotFoundError("qwen3 서버를 찾을 수 없습니다.")

        provider = QwenLLMProvider(base_url=runpod.address)
        model_name = "qwen3-vl:8b"

        logger.info(f"Qwen LLM 프로바이더 생성 완료 (모델: {model_name})")
        return provider, model_name

    @staticmethod
    def _create_gpt_provider() -> tuple[GPTLLMProvider, str]:
        """
        GPT LLM 프로바이더 생성 (OpenAI 기반)

        Returns:
            Tuple[GPTLLMProvider, str]: (GPT 프로바이더, 모델명)

        Raises:
            ValueError: OpenAI API 키가 설정되지 않은 경우
        """
        if not settings.openai_api_key:
            logger.error("OPENAI_API_KEY가 설정되지 않았습니다.")
            raise ValueError("OPENAI_API_KEY 환경 변수가 필요합니다.")

        provider = GPTLLMProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_model
        )
        model_name = settings.openai_model

        logger.info(f"GPT LLM 프로바이더 생성 완료 (모델: {model_name})")
        return provider, model_name
