"""Chain Summary Request Schemas"""
from pydantic import BaseModel, Field
from typing import Optional
from app.core.types import IntFromStr
from ...constants import DEFAULT_CHAIN_SUMMARY_PROMPT


class StoreInfo(BaseModel):
    """매장 정보"""
    안경원명: str = Field(..., description="안경원 이름")
    매장번호: str = Field(..., description="매장 전화번호")
    대표자명: str = Field(..., description="대표자 이름")


class MonthlySalesRecord(BaseModel):
    """월별 매출 레코드"""
    년월: str = Field(..., description="년월 (YYYY-MM)")
    판매금액: IntFromStr = Field(..., ge=0, description="판매금액")
    할인액: IntFromStr = Field(0, ge=0, description="할인액")
    결제금액: IntFromStr = Field(..., ge=0, description="결제금액 (실판매금액)")
    판매_수: IntFromStr = Field(..., ge=0, description="판매 수", alias="판매 수")
    반품_수: Optional[IntFromStr] = Field(None, ge=0, description="반품 수", alias="반품 수")
    납부_수: IntFromStr = Field(0, ge=0, description="납부 수", alias="납부 수")

    class Config:
        populate_by_name = True  # alias와 원본 필드명 둘 다 허용
        json_schema_extra = {
            "example": {
                "년월": "2024-02",
                "판매금액": 50807800,
                "할인액": 1022800,
                "결제금액": 50208000,
                "판매 수": 487,
                "반품 수": None,
                "납부 수": 51
            }
        }


class WeeklyPatternRecord(BaseModel):
    """요일/시간대별 패턴 레코드"""
    W: str = Field(..., description="요일 코드 (1=일요일, 2=월요일, ..., 7=토요일)")
    WEEK: str = Field(..., description="요일명 (일, 월, 화, 수, 목, 금, 토)")
    HOUR: str = Field(..., description="시간대 (0-23)")
    방문수: IntFromStr = Field(..., ge=0, description="방문 수")
    판매금액: IntFromStr = Field(..., ge=0, description="판매 금액")

    class Config:
        json_schema_extra = {
            "example": {
                "W": "3",
                "WEEK": "화",
                "HOUR": "15",
                "방문수": 7,
                "판매금액": 1111000
            }
        }


class CustomerDemographicRecord(BaseModel):
    """고객 연령대별 레코드"""
    년월: str = Field(..., description="년월 (YYYY-MM)")
    AGE: IntFromStr = Field(..., ge=-1, le=9, description="연령 코드 (-1=미분류, 0=10대미만, 1=10대, 2=20대, ..., 9=90대)")
    첫방문여부: IntFromStr = Field(..., ge=0, le=1, description="첫방문 여부 (0=재방문, 1=첫방문)")
    건수: IntFromStr = Field(..., ge=0, description="구매 건수")
    판매금액: IntFromStr = Field(..., ge=0, description="판매 금액")

    class Config:
        json_schema_extra = {
            "example": {
                "년월": "2025-07",
                "AGE": 2,
                "첫방문여부": 0,
                "건수": 19,
                "판매금액": 1698000
            }
        }


class ProductRecord(BaseModel):
    """상품별 판매 레코드"""
    상품명: Optional[str] = Field(None, description="상품명")
    판매_수: IntFromStr = Field(..., ge=0, description="판매 수량", alias="판매 수")
    판매금액합: IntFromStr = Field(..., ge=0, description="판매 금액 합계")
    브랜드명: str = Field("", description="브랜드명 (없으면 빈 문자열)")
    상품구분: str = Field(..., description="상품 구분 (예: 선글라스/안경테, 콘택트렌즈, 안경렌즈)")

    class Config:
        populate_by_name = True  # alias와 원본 필드명 둘 다 허용
        json_schema_extra = {
            "example": {
                "상품명": "스타일 선글라스",
                "판매 수": 1,
                "판매금액합": 49000,
                "브랜드명": "",
                "상품구분": "선글라스/안경테"
            }
        }


class SalesData(BaseModel):
    """월별 매출 데이터"""
    name: str = Field(..., description="데이터 설명 (예: 작년부터 지난달까지)")
    data: list[MonthlySalesRecord] = Field(..., description="월별 매출 내역")


class WeekData(BaseModel):
    """요일/시간대별 데이터"""
    name: str = Field(..., description="데이터 설명 (예: 지난달 일~토)")
    data: list[WeeklyPatternRecord] = Field(..., description="요일별/시간대별 데이터")


class CustomerData(BaseModel):
    """고객 연령대별 데이터"""
    name: str = Field(..., description="데이터 설명 (예: 3개월 고객 연령대,신규/재방문)")
    data: list[CustomerDemographicRecord] = Field(..., description="연령대별 데이터")


class ProductData(BaseModel):
    """상품별 데이터"""
    name: str = Field(..., description="데이터 설명 (예: 지난달 브랜드,상품구분별 상품정보)")
    data: list[ProductRecord] = Field(..., description="상품 데이터")


class ChainSummaryDataRequest(BaseModel):
    """체인 매출 데이터 요청 스키마 (info, sales, week, customer, product를 포함)"""
    
class ChainSummaryDataRequest(BaseModel):
    """체인 매출 데이터 요청 스키마 (info, sales, week, customer, product를 포함)"""
    
    info: StoreInfo = Field(..., description="매장 정보")
    sales: SalesData = Field(..., description="월별 매출 데이터")
    week: WeekData = Field(..., description="요일/시간대별 방문 및 매출 데이터")
    customer: CustomerData = Field(..., description="고객 연령대별 데이터")
    product: ProductData = Field(..., description="상품별 판매 데이터")


class ChainSummaryRequest(BaseModel):
    """
    체인 매니저 매출 요약 리포트 생성 요청 스키마

    custom_prompt와 json_content를 포함하는 최상위 요청 구조
    """
    custom_prompt: Optional[str] = Field(
        default=None,
        description="AI 인사이트 생성을 위한 커스텀 프롬프트 (선택사항). 미입력 시 기본 프롬프트 사용"
    )
    json_content: ChainSummaryDataRequest = Field(..., alias="json", description="매장 정보와 매출 데이터를 포함한 데이터 객체")

    class Config:
        populate_by_name = True  # alias와 원본 필드명 둘 다 허용
        json_schema_extra = {
            "example": {
                "custom_prompt": DEFAULT_CHAIN_SUMMARY_PROMPT,
                "json": {
                    "info": {
                        "안경원명": "히비스 안경원",
                        "매장번호": "02-1234-1234",
                        "대표자명": "김안경"
                    },
                    "sales": {
                        "name": "작년부터 지난달까지",
                        "data": [
                            {
                                "년월": "2024-02",
                                "판매금액": 50807800,
                                "할인액": 1022800,
                                "결제금액": 50208000,
                                "판매 수": 487,
                                "반품 수": None,
                                "납부 수": 51
                            }
                        ]
                    },
                    "week": {
                        "name": "지난달 일~토",
                        "data": [
                            {
                                "W": "3",
                                "WEEK": "화",
                                "HOUR": "15",
                                "방문수": 7,
                                "판매금액": 1111000
                            }
                        ]
                    },
                    "customer": {
                        "name": "3개월 고객 연령대,신규/재방문",
                        "data": [
                            {
                                "년월": "2025-07",
                                "AGE": 2,
                                "첫방문여부": 0,
                                "건수": 19,
                                "판매금액": 1698000
                            }
                        ]
                    },
                    "product": {
                        "name": "지난달 브랜드,상품구분별 상품정보",
                        "data": [
                            {
                                "상품명": "스타일 선글라스",
                                "판매 수": 1,
                                "판매금액합": 49000,
                                "브랜드명": "",
                                "상품구분": "선글라스/안경테"
                            }
                        ]
                    }
                }
            }
        }
