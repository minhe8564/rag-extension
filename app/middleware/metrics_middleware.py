"""
응답 시간 측정 미들웨어 및 데코레이터
"""
import time
from functools import wraps
from typing import Callable, Any, Optional
from fastapi import Request
from app.service.extract_metrics_service import get_extract_metrics_service
from loguru import logger


def extract_metrics_timing(
    strategy_extractor: Optional[Callable] = None,
    file_type_extractor: Optional[Callable] = None
):
    """
    Extract 엔드포인트 응답 시간 측정 데코레이터
    
    Args:
        strategy_extractor: strategy를 추출하는 함수 (request 또는 함수 인자에서)
        file_type_extractor: file_type을 추출하는 함수 (request 또는 함수 인자에서)
    
    Usage:
        @extract_metrics_timing(
            strategy_extractor=lambda request: request.extractionStrategy,
            file_type_extractor=lambda request: request.fileType
        )
        async def extract_process(request: ExtractProcessRequest):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            metrics_service = get_extract_metrics_service()
            start_time = time.perf_counter()
            
            # strategy와 file_type 추출 시도
            strategy = None
            file_type = None
            
            try:
                # 함수 인자에서 추출 시도
                if strategy_extractor:
                    try:
                        # 첫 번째 인자가 request 객체일 가능성
                        if args and hasattr(args[0], 'extractionStrategy'):
                            strategy = args[0].extractionStrategy
                        elif 'request' in kwargs:
                            strategy = strategy_extractor(kwargs['request'])
                        elif args:
                            strategy = strategy_extractor(args[0])
                    except Exception:
                        pass
                
                if file_type_extractor:
                    try:
                        if args and hasattr(args[0], 'fileType'):
                            file_type = args[0].fileType
                        elif 'request' in kwargs:
                            file_type = file_type_extractor(kwargs['request'])
                        elif args:
                            file_type = file_type_extractor(args[0])
                    except Exception:
                        pass
                
                # 함수 실행
                result = await func(*args, **kwargs)
                
                # 응답 시간 계산 및 메트릭 기록
                total_time_ms = (time.perf_counter() - start_time) * 1000
                
                # result에서 strategy, file_type 추출 시도 (함수 인자에서 못 찾은 경우)
                if not strategy or not file_type:
                    if hasattr(result, 'result'):
                        result_obj = result.result
                        if not strategy and hasattr(result_obj, 'strategy'):
                            strategy = result_obj.strategy
                        if not file_type and hasattr(result_obj, 'fileType'):
                            file_type = result_obj.fileType
                
                # 메트릭 기록
                await metrics_service.record_extract_time(
                    time_ms=total_time_ms,
                    strategy=strategy,
                    file_type=file_type
                )
                
                logger.info(
                    f"Extract completed in {total_time_ms:.2f}ms "
                    f"(strategy: {strategy}, file_type: {file_type})"
                )
                
                return result
                
            except Exception as e:
                # 에러 발생 시에도 시간 측정
                total_time_ms = (time.perf_counter() - start_time) * 1000
                logger.error(
                    f"Extract failed after {total_time_ms:.2f}ms: {str(e)}"
                )
                # 에러는 그대로 전파
                raise
        
        return wrapper
    return decorator


# 간단한 버전: 자동으로 request에서 추출
def with_extract_metrics(func: Callable) -> Callable:
    """
    Extract 엔드포인트 응답 시간 측정 데코레이터
    
    함수의 첫 번째 인자에서 extractionStrategy와 fileType을 자동으로 추출합니다.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        metrics_service = get_extract_metrics_service()
        start_time = time.perf_counter()
        
        strategy = None
        file_type = None
        
        try:
            # 첫 번째 인자에서 추출 시도
            if args:
                request_or_first_arg = args[0]
                
                # ExtractProcessRequest인 경우
                if hasattr(request_or_first_arg, 'extractionStrategy'):
                    strategy = request_or_first_arg.extractionStrategy
                
                # Form 데이터인 경우 (extract_test)
                # kwargs에서 extractionStrategy 찾기
                if not strategy and 'extractionStrategy' in kwargs:
                    strategy = kwargs['extractionStrategy']
            
            # 함수 실행
            result = await func(*args, **kwargs)
            
            # 응답 시간 계산
            total_time_ms = (time.perf_counter() - start_time) * 1000
            
            # result에서 file_type과 strategy 추출
            if hasattr(result, 'result'):
                result_obj = result.result
                if hasattr(result_obj, 'fileType'):
                    file_type = result_obj.fileType
                if not strategy and hasattr(result_obj, 'strategy'):
                    strategy = result_obj.strategy
            
            # file_type을 파일명에서 추출 시도 (extract_test의 경우)
            if not file_type and args:
                # UploadFile이 있는 경우
                for arg in args:
                    if hasattr(arg, 'filename'):
                        filename = arg.filename or "unknown"
                        file_ext = filename.split('.')[-1].lower() if '.' in filename else ""
                        if file_ext:
                            file_type = file_ext
                            break
            
            # 메트릭 기록
            await metrics_service.record_extract_time(
                time_ms=total_time_ms,
                strategy=strategy,
                file_type=file_type
            )
            
            logger.info(
                f"Extract completed in {total_time_ms:.2f}ms "
                f"(strategy: {strategy}, file_type: {file_type})"
            )
            
            return result
            
        except Exception as e:
            # 에러 발생 시에도 시간 측정
            total_time_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"Extract failed after {total_time_ms:.2f}ms: {str(e)}"
            )
            raise
    
    return wrapper
