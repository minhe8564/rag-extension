"""AdminSchool API Client - 외부 안경원 데이터 API 클라이언트"""
import httpx
from typing import Optional
from app.core.config import settings


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
            httpx.HTTPError: API 호출 실패 시
        """
        url = f"{self.base_url}/ssafy/opt_stat/{store_id}"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

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
