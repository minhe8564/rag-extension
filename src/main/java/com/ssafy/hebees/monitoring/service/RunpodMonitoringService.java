package com.ssafy.hebees.monitoring.service;

import com.ssafy.hebees.monitoring.client.RunpodMonitoringClient;
import com.ssafy.hebees.monitoring.dto.response.RunpodCpuUsageResponse;
import com.ssafy.hebees.monitoring.dto.response.RunpodGpuUsageResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

@Slf4j
@Service
@RequiredArgsConstructor
public class RunpodMonitoringService {

    private final RunpodMonitoringClient runpodMonitoringClient;

    /**
     * Runpod Pod의 GPU 사용량 조회
     *
     * @param podId Pod ID
     * @return GPU 사용량 정보
     */
    public RunpodGpuUsageResponse getGpuUsage(String podId) {
        return runpodMonitoringClient.getGpuUsage(podId);
    }

    /**
     * Runpod Pod의 CPU 사용량 조회
     *
     * @param podId Pod ID
     * @return CPU 사용량 정보
     */
    public RunpodCpuUsageResponse getCpuUsage(String podId) {
        return runpodMonitoringClient.getCpuUsage(podId);
    }
}
