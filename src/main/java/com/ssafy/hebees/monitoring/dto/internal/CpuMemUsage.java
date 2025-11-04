package com.ssafy.hebees.monitoring.dto.internal;

/**
 * CPU 및 메모리 사용량 정보를 담는 내부 DTO
 */
public record CpuMemUsage(
    double cpuUsage,
    double memoryUsage,
    boolean available
) {

    public static CpuMemUsage unavailable() {
        return new CpuMemUsage(0.0, 0.0, false);
    }
}

