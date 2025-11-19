"""
시스템 모니터링 서비스
CPU 사용률 등 시스템 리소스 모니터링
"""
import asyncio
import logging
from typing import AsyncIterator, Union, Optional
from datetime import datetime, timezone, timedelta
import json

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logging.warning("psutil이 설치되지 않았습니다. CPU 모니터링 기능을 사용할 수 없습니다.")

from ..schemas.cpu_response import CpuUsageResponse
from ..schemas.memory_response import MemoryUsageResponse
from ..schemas.network_response import NetworkTrafficResponse

logger = logging.getLogger(__name__)

# 한국 시간대
KST = timezone(timedelta(hours=9))

class MonitoringService:
    """시스템 리소스 모니터링 서비스"""
    
    def __init__(self):
        if not PSUTIL_AVAILABLE:
            raise ImportError("psutil이 필요합니다. 'pip install psutil'로 설치해주세요.")
    
    def _get_kst_timestamp(self) -> str:
        now = datetime.now(KST)
        timestamp_str = now.strftime("%Y-%m-%dT%H:%M:%S%z")
        if len(timestamp_str) > 10 and timestamp_str[-5] in ['+', '-']:
            timestamp_str = timestamp_str[:-2] + ':' + timestamp_str[-2:]
        return timestamp_str
    
    def _calculate_active_cores(self, total_cores: int, cpu_percent: float) -> int:
        return round(total_cores * cpu_percent / 100)
    
    def _get_cpu_data(self, interval: Optional[float] = None) -> CpuUsageResponse:
        """CPU 사용률 데이터 조회 및 DTO 생성"""
        cpu_percent = psutil.cpu_percent(interval=interval)
        total_cores = psutil.cpu_count()
        active_cores = self._calculate_active_cores(total_cores, cpu_percent)
        
        return CpuUsageResponse(
            timestamp=self._get_kst_timestamp(),
            cpuUsagePercent=round(cpu_percent, 1),
            totalCores=total_cores,
            activeCores=active_cores
        )
    
    async def stream_cpu_usage(self) -> AsyncIterator[str]:
        try:
            # 초기 연결 시 init 이벤트 전송
            init_data = self._get_cpu_data(interval=0.1)
            yield self._format_sse_event("init", init_data)
            
            while True:
                await asyncio.sleep(1.0)  # 1초마다 업데이트
                update_data = self._get_cpu_data(interval=None)
                yield self._format_sse_event("update", update_data)
                
        except asyncio.CancelledError:
            logger.info("CPU 사용률 스트리밍이 취소되었습니다.")
        except Exception as e:
            logger.error(f"CPU 사용률 스트리밍 중 오류 발생: {e}", exc_info=True)
            error_data = {"error": str(e)}
            yield self._format_sse_event("error", error_data)
    
    def _bytes_to_gb(self, bytes_value: int) -> float:
        """바이트를 GB로 변환"""
        return round(bytes_value / (1024 ** 3), 1)
    
    def _calculate_memory_usage_percent(self, used_gb: float, total_gb: float) -> float:
        """메모리 사용률 계산: (usedMemoryGB / totalMemoryGB) * 100"""
        if total_gb == 0:
            return 0.0
        return round((used_gb / total_gb) * 100, 1)
    
    def _get_memory_data(self) -> MemoryUsageResponse:
        """메모리 사용량 데이터 조회 및 DTO 생성"""
        memory = psutil.virtual_memory()
        total_memory_gb = self._bytes_to_gb(memory.total)
        used_memory_gb = self._bytes_to_gb(memory.used)
        memory_usage_percent = self._calculate_memory_usage_percent(used_memory_gb, total_memory_gb)
        
        return MemoryUsageResponse(
            timestamp=self._get_kst_timestamp(),
            totalMemoryGB=total_memory_gb,
            usedMemoryGB=used_memory_gb,
            memoryUsagePercent=memory_usage_percent
        )
    
    async def stream_memory_usage(self) -> AsyncIterator[str]:
        try:
            # 초기 연결 시 init 이벤트 전송
            init_data = self._get_memory_data()
            yield self._format_sse_event("init", init_data)
            
            while True:
                await asyncio.sleep(1.0)  # 1초마다 업데이트
                update_data = self._get_memory_data()
                yield self._format_sse_event("update", update_data)
                
        except asyncio.CancelledError:
            logger.info("메모리 사용률 스트리밍이 취소되었습니다.")
        except Exception as e:
            logger.error(f"메모리 사용률 스트리밍 중 오류 발생: {e}", exc_info=True)
            error_data = {"error": str(e)}
            yield self._format_sse_event("error", error_data)
    
    def _bytes_to_mbps(self, bytes_value: int, seconds: float) -> float:
        """바이트를 Mbps로 변환 (시간 간격 포함)"""
        if seconds == 0:
            return 0.0
        return round((bytes_value * 8) / seconds / (1024 * 1024), 1)
    
    def _detect_network_bandwidth(self) -> Optional[float]:
        try:
            if_stats = psutil.net_if_stats()
            
            max_speed_mbps = 0.0
            for interface_name, stats in if_stats.items():
                if stats.isup and stats.speed > 0:
                    if stats.speed > 1000000:
                        speed_mbps = stats.speed / (1024 * 1024)  # bps -> Mbps
                    elif stats.speed > 1000:
                        speed_mbps = stats.speed
                    else:
                        speed_mbps = stats.speed * 1000
                    
                    if speed_mbps > max_speed_mbps:
                        max_speed_mbps = speed_mbps
                        logger.debug(f"인터페이스 '{interface_name}' 속도: {speed_mbps:.1f} Mbps (원본: {stats.speed})")
            
            if max_speed_mbps > 0:
                logger.info(f"네트워크 대역폭 자동 감지: {max_speed_mbps:.1f} Mbps")
                return round(max_speed_mbps, 1)
            else:
                logger.warning("네트워크 대역폭 자동 감지 실패: 감지된 인터페이스가 없습니다.")
                return None
        except Exception as e:
            logger.warning(f"네트워크 대역폭 자동 감지 중 오류 발생: {e}")
            return None
    
    def _get_network_bandwidth(self) -> float:
        """네트워크 대역폭 조회 (자동 감지 또는 설정값)"""
        detected_bandwidth = self._detect_network_bandwidth()
        if detected_bandwidth is not None:
            return detected_bandwidth
        else:
            from app.core.config.settings import settings
            bandwidth_mbps = settings.network_bandwidth_mbps
            logger.info(f"설정값 사용: {bandwidth_mbps} Mbps")
            return bandwidth_mbps
    
    def _get_network_data(
        self, 
        bytes_sent: int, 
        bytes_recv: int, 
        bandwidth_mbps: float,
        interval_seconds: float = 5.0
    ) -> NetworkTrafficResponse:
        """네트워크 트래픽 데이터 조회 및 DTO 생성"""
        inbound_mbps = self._bytes_to_mbps(bytes_recv, interval_seconds)
        outbound_mbps = self._bytes_to_mbps(bytes_sent, interval_seconds)
        
        return NetworkTrafficResponse(
            timestamp=self._get_kst_timestamp(),
            inboundMbps=inbound_mbps,
            outboundMbps=outbound_mbps,
            bandwidthMbps=bandwidth_mbps
        )
    
    async def stream_network_traffic(self, bandwidth_mbps: Optional[float] = None) -> AsyncIterator[str]:
        try:
            # 대역폭 설정
            if bandwidth_mbps is None:
                bandwidth_mbps = self._get_network_bandwidth()
            
            # 초기 연결 시 init 이벤트 전송
            initial_counters = psutil.net_io_counters()
            initial_bytes_sent = initial_counters.bytes_sent
            initial_bytes_recv = initial_counters.bytes_recv
            
            # 초기값은 0으로 설정
            init_data = NetworkTrafficResponse(
                timestamp=self._get_kst_timestamp(),
                inboundMbps=0.0,
                outboundMbps=0.0,
                bandwidthMbps=bandwidth_mbps
            )
            
            yield self._format_sse_event("init", init_data)
            
            # 5초 간격으로 업데이트
            await asyncio.sleep(5.0)
            
            while True:
                # 현재 측정
                current_counters = psutil.net_io_counters()
                current_bytes_sent = current_counters.bytes_sent
                current_bytes_recv = current_counters.bytes_recv
                
                # 5초 동안의 변화량 계산
                bytes_sent_diff = current_bytes_sent - initial_bytes_sent
                bytes_recv_diff = current_bytes_recv - initial_bytes_recv
                
                # 데이터 생성 및 전송
                update_data = self._get_network_data(
                    bytes_sent_diff,
                    bytes_recv_diff,
                    bandwidth_mbps,
                    interval_seconds=5.0
                )
                
                yield self._format_sse_event("update", update_data)
                
                # 다음 측정을 위해 업데이트
                initial_bytes_sent = current_bytes_sent
                initial_bytes_recv = current_bytes_recv
                
                # 5초 대기
                await asyncio.sleep(5.0)
                
        except asyncio.CancelledError:
            logger.info("네트워크 트래픽 스트리밍이 취소되었습니다.")
        except Exception as e:
            logger.error(f"네트워크 트래픽 스트리밍 중 오류 발생: {e}", exc_info=True)
            error_data = {"error": str(e)}
            yield self._format_sse_event("error", error_data)
    
    def _format_sse_event(
        self, 
        event_type: str, 
        data: Union[CpuUsageResponse, MemoryUsageResponse, NetworkTrafficResponse, dict]
    ) -> str:
        if isinstance(data, (CpuUsageResponse, MemoryUsageResponse, NetworkTrafficResponse)):
            json_data = json.dumps(data.model_dump(), ensure_ascii=False)
        else:
            json_data = json.dumps(data, ensure_ascii=False)
        
        return f"event: {event_type}\ndata: {json_data}\n\n"

