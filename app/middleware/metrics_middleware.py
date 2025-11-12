"""
응답 시간 측정 미들웨어 및 데코레이터
"""
import time
from functools import wraps
from typing import Callable
from app.service.search_metrics_service import get_search_metrics_service
from loguru import logger


def with_search_metrics(func: Callable) -> Callable:
    """
    Search 엔드포인트 응답 시간 측정 데코레이터
    
    함수의 첫 번째 인자(SearchProcessRequest)에서 searchStrategy를 자동으로 추출합니다.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        metrics_service = get_search_metrics_service()
        start_time = time.perf_counter()
        
        strategy = None
        
        try:
            # 첫 번째 인자에서 strategy 추출 시도
            if args:
                request = args[0]
                
                # SearchProcessRequest인 경우
                if hasattr(request, 'searchStrategy'):
                    strategy = request.searchStrategy
            
            # 함수 실행
            result = await func(*args, **kwargs)
            
            # 응답 시간 계산
            total_time_ms = (time.perf_counter() - start_time) * 1000
            
            # result에서 strategy 추출 시도 (함수 인자에서 못 찾은 경우)
            if not strategy and hasattr(result, 'result'):
                result_obj = result.result
                if hasattr(result_obj, 'strategy'):
                    strategy = result_obj.strategy
            
            # 메트릭 기록
            await metrics_service.record_search_time(
                time_ms=total_time_ms,
                strategy=strategy
            )
            
            logger.info(
                f"Search completed in {total_time_ms:.2f}ms "
                f"(strategy: {strategy})"
            )
            
            return result
            
        except Exception as e:
            # 에러 발생 시에도 시간 측정
            total_time_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"Search failed after {total_time_ms:.2f}ms: {str(e)}"
            )
            raise
    
    return wrapper
