"""Sales Report Custom Exceptions"""


class SalesReportException(Exception):
    """매출 리포트 관련 기본 예외"""
    pass


class ExternalAPIError(SalesReportException):
    """외부 API 호출 실패"""
    pass


class DataValidationError(SalesReportException):
    """데이터 검증 실패"""
    pass


class LLMServiceError(SalesReportException):
    """LLM 서비스 오류"""
    pass


class RunpodNotFoundError(SalesReportException):
    """Runpod 서버를 찾을 수 없음"""
    pass
