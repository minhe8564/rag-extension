"""Sales Report Response Schemas"""
from app.domains.sales_report.schemas.response.store_summary_response import (
    StoreSummaryResponse,
    MonthlySalesReport,
    DailySalesReport,
    PaymentBreakdown,
    TopCustomer,
    ReceivableCustomer,
    StoreInfo,
    LLMInsights as StoreLLMInsights,
    Metadata as StoreMetadata
)
from app.domains.sales_report.schemas.response.chain_summary_response import (
    ChainSummaryResponse,
    AnalysisPeriod,
    StorePerformance,
    ProductInsights,
    TimePatterns,
    CustomerAnalysis,
    TopProduct,
    TopBrand,
    CategoryRevenue,
    RevenueDistribution,
    WeeklyPattern,
    HourlyPattern,
    PeakInsights,
    CustomerDemographic,
    KeySegments,
    VisitSalesPattern,
    LLMInsights as ChainLLMInsights,
    Metadata as ChainMetadata
)

__all__ = [
    # Store Summary
    "StoreSummaryResponse",
    "MonthlySalesReport",
    "DailySalesReport",
    "PaymentBreakdown",
    "TopCustomer",
    "ReceivableCustomer",
    "StoreInfo",
    "StoreLLMInsights",
    "StoreMetadata",
    # Chain Summary
    "ChainSummaryResponse",
    "AnalysisPeriod",
    "StorePerformance",
    "ProductInsights",
    "TimePatterns",
    "CustomerAnalysis",
    "TopProduct",
    "TopBrand",
    "CategoryRevenue",
    "RevenueDistribution",
    "WeeklyPattern",
    "HourlyPattern",
    "PeakInsights",
    "CustomerDemographic",
    "KeySegments",
    "VisitSalesPattern",
    "ChainLLMInsights",
    "ChainMetadata"
]
