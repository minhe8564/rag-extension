package com.ssafy.hebees.monitoring.service;

import com.ssafy.hebees.monitoring.dto.response.CpuUsageResponse;
import com.ssafy.hebees.monitoring.dto.response.MemoryUsageResponse;
import com.ssafy.hebees.monitoring.dto.response.NetworkTrafficResponse;
import com.ssafy.hebees.monitoring.dto.response.RunpodCpuUsageResponse;
import com.ssafy.hebees.monitoring.dto.response.RunpodGpuUsageResponse;
import com.ssafy.hebees.monitoring.dto.response.ServicePerformanceListResponse;
import com.ssafy.hebees.monitoring.dto.response.ServiceStatusListResponse;
import com.ssafy.hebees.monitoring.dto.response.StorageListResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.http.codec.ServerSentEvent;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Flux;

/**
 * 모니터링 서비스 Facade 각 모니터링 서비스들을 통합하여 컨트롤러에 제공하는 역할
 */
@Service
@RequiredArgsConstructor
public class MonitoringService {

    private final CpuMonitoringService cpuMonitoringService;
    private final MemoryMonitoringService memoryMonitoringService;
    private final NetworkMonitoringService networkMonitoringService;
    private final ServiceMonitoringService serviceMonitoringService;
    private final DiskMonitoringService diskMonitoringService;
    private final RunpodMonitoringService runpodMonitoringService;

    // CPU Monitoring
    public Flux<ServerSentEvent<CpuUsageResponse>> streamCpuUsage() {
        return cpuMonitoringService.streamCpuUsage();
    }

    // Memory Monitoring
    public Flux<ServerSentEvent<MemoryUsageResponse>> streamMemoryUsage() {
        return memoryMonitoringService.streamMemoryUsage();
    }

    // Network Monitoring
    public Flux<ServerSentEvent<NetworkTrafficResponse>> streamNetworkTraffic() {
        return networkMonitoringService.streamNetworkTraffic();
    }

    // Service Monitoring
    public ServicePerformanceListResponse getServicePerformance() {
        return serviceMonitoringService.getServicePerformance();
    }

    // Service Monitoring
    public ServiceStatusListResponse getServiceStatus() {
        return serviceMonitoringService.getServiceStatus();
    }

    // Disk Monitoring
    public StorageListResponse getStorageInfo() {
        return diskMonitoringService.getStorageInfo();
    }

    // Runpod Monitoring
    public RunpodGpuUsageResponse getRunpodGpuUsage(String podId) {
        return runpodMonitoringService.getGpuUsage(podId);
    }

    public RunpodCpuUsageResponse getRunpodCpuUsage(String podId) {
        return runpodMonitoringService.getCpuUsage(podId);
    }
}
