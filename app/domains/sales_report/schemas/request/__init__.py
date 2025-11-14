"""Sales Report Request Schemas"""
from app.domains.sales_report.schemas.request.store_summary_request import (
    StoreInfoRequest,
    TransactionRequest,
    StoreSummaryRequest
)
from app.domains.sales_report.schemas.request.chain_summary_request import (
    ChainSummaryRequest,
    StoreInfo,
    MonthlySalesRecord,
    WeeklyPatternRecord,
    CustomerDemographicRecord,
    ProductRecord,
    SalesData,
    WeekData,
    CustomerData,
    ProductData
)

__all__ = [
    # Store Summary
    "StoreInfoRequest",
    "TransactionRequest",
    "StoreSummaryRequest",
    # Chain Summary
    "ChainSummaryRequest",
    "StoreInfo",
    "MonthlySalesRecord",
    "WeeklyPatternRecord",
    "CustomerDemographicRecord",
    "ProductRecord",
    "SalesData",
    "WeekData",
    "CustomerData",
    "ProductData"
]
