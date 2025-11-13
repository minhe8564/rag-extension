"""AdminSchool API Client - 외부 안경원 데이터 API 클라이언트"""
import httpx
import logging
from typing import Optional
from app.core.config import settings
from app.domains.sales_report.exceptions import ExternalAPIError

logger = logging.getLogger(__name__)


class AdminSchoolClient:
    """AdminSchool API 클라이언트"""

    def __init__(self):
        self.base_url = "https://napi.adminschool.net"
        self.timeout = 30.0

    async def fetch_sales_data(self, store_id: str) -> dict:
        """
        안경원 판매 데이터 조회

        Args:
            store_id: 안경원 ID (예: "6266")

        Returns:
            dict: 판매 데이터 (info, data 포함)

        Raises:
            ExternalAPIError: API 호출 실패 시
        """
        url = f"{self.base_url}/ssafy/opt_stat/{store_id}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException as e:
            logger.error(f"AdminSchool API 타임아웃: {store_id}", exc_info=True)
            raise ExternalAPIError(f"외부 API 응답 시간 초과 (30초): {str(e)}")
        except httpx.HTTPStatusError as e:
            logger.error(f"AdminSchool API HTTP 오류: {e.response.status_code}", exc_info=True)
            raise ExternalAPIError(f"외부 API 호출 실패 (상태 코드: {e.response.status_code}): {str(e)}")
        except httpx.RequestError as e:
            logger.error(f"AdminSchool API 요청 오류: {str(e)}", exc_info=True)
            raise ExternalAPIError(f"외부 API 연결 실패: {str(e)}")
        except Exception as e:
            logger.error(f"AdminSchool API 예상치 못한 오류: {str(e)}", exc_info=True)
            raise ExternalAPIError(f"외부 API 호출 중 오류 발생: {str(e)}")

    async def fetch_sales_data_by_period(
        self,
        store_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> dict:
        """
        기간별 판매 데이터 조회 (미래 확장용)

        Args:
            store_id: 안경원 ID
            start_date: 시작일 (YYYY-MM-DD)
            end_date: 종료일 (YYYY-MM-DD)

        Returns:
            dict: 판매 데이터
        """
        # 현재는 전체 데이터를 가져온 후 필터링
        # 추후 API가 기간 파라미터를 지원하면 수정
        data = await self.fetch_sales_data(store_id)

        if start_date or end_date:
            # 기간 필터링 로직 (서비스 레이어에서 처리 예정)
            pass

        return data
