"""Store Summary Request Schemas"""
from pydantic import BaseModel, Field, model_validator
from typing import List, Any, Optional
from datetime import datetime
from ...constants import DEFAULT_STORE_SUMMARY_PROMPT


class StoreInfoRequest(BaseModel):
    """매장 정보 요청 스키마 (한글/영문 필드명 모두 지원)"""
    store_name: str = Field(..., alias="안경원명", description="안경원명")
    store_phone: str = Field(..., alias="매장번호", description="매장번호")
    owner_name: str = Field(..., alias="대표자명", description="대표자명")

    class Config:
        populate_by_name = True  # 한글/영문 필드명 모두 허용
        json_schema_extra = {
            "example": {
                "안경원명": "행복안경원",
                "매장번호": "02-1234-5678",
                "대표자명": "홍길동"
            }
        }


class TransactionRequest(BaseModel):
    """거래 데이터 요청 스키마 (AdminSchool API 형식과 동일)"""
    # 유연하게 모든 필드를 받을 수 있도록 설정
    class Config:
        extra = "allow"  # 추가 필드 허용


class StoreSummaryRequest(BaseModel):
    """
    개별 안경원 매출 요약 리포트 생성 요청 스키마

    AdminSchool API에서 가져온 전체 데이터를 그대로 전달
    year_month가 없으면 data 배열의 첫 번째 거래 날짜에서 자동 추출
    """
    info: StoreInfoRequest = Field(..., description="매장 정보")
    data: List[dict] = Field(..., description="거래 데이터 리스트")
    year_month: Optional[str] = Field(None, description="리포트 기준 년월 (YYYY-MM), 미입력 시 자동 추출")
    custom_prompt: Optional[str] = Field(
        default=None,
        description="AI 요약 생성을 위한 커스텀 프롬프트 (선택사항). 미입력 시 기본 프롬프트 사용"
    )

    @model_validator(mode='after')
    def extract_year_month(self):
        """year_month가 없으면 data에서 자동 추출"""
        if self.year_month is None and self.data:
            # data 배열에서 날짜 필드 찾기 (판매일자, 거래일시 등)
            first_transaction = self.data[0]
            date_str = None

            # 가능한 날짜 필드명들 확인
            for field_name in ['판매일자', '거래일시', 'date', 'transaction_date']:
                if field_name in first_transaction:
                    date_str = str(first_transaction[field_name])
                    break

            if date_str:
                # 날짜 문자열에서 YYYY-MM 추출
                try:
                    # "2025-10-01" 또는 "2025-10-01 10:30:00" 형식 처리
                    parsed_date = datetime.strptime(date_str.split()[0], "%Y-%m-%d")
                    self.year_month = parsed_date.strftime("%Y-%m")
                except ValueError as e:
                    # 파싱 실패 시 명시적으로 에러 발생
                    raise ValueError(
                        f"날짜 파싱 실패: '{date_str}' 형식이 올바르지 않습니다. "
                        f"YYYY-MM-DD 형식이어야 합니다."
                    )
            else:
                # 날짜 필드가 없으면 명시적으로 에러 발생
                raise ValueError(
                    "year_month가 지정되지 않았고, 데이터에서 날짜 필드를 찾을 수 없습니다. "
                    "다음 필드 중 하나가 필요합니다: 판매일자, 거래일시, date, transaction_date"
                )

        return self

    class Config:
        json_schema_extra = {
            "example": {
                "info": {
                    "store_name": "행복안경원",
                    "store_phone": "02-1234-5678",
                    "owner_name": "홍길동"
                },
                "data": [
                    {
                        "거래일시": "2024-11-01 10:30:00",
                        "고객명": "김철수",
                        "카드": 150000,
                        "현금": 0,
                        "현금영수": 0,
                        "상품권금액": 0,
                        "미수금": 0,
                        "고객연락처": "010-1234-5678"
                    },
                    {
                        "거래일시": "2024-11-02 14:20:00",
                        "고객명": "이영희",
                        "카드": 0,
                        "현금": 200000,
                        "현금영수": 200000,
                        "상품권금액": 0,
                        "미수금": 0,
                        "고객연락처": "010-9876-5432"
                    }
                ],
                "year_month": "2024-11",
                "custom_prompt": DEFAULT_STORE_SUMMARY_PROMPT
            }
        }
