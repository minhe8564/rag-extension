package com.ssafy.hebees.monitoring.client;

import java.time.Instant;
import java.util.Set;

/**
 * cAdvisor 컨테이너 메트릭
 */
public record CadvisorContainerMetrics(
    String canonicalName,
    Set<String> aliases,
    boolean running,
    double cpuPercent,
    double memoryPercent,
    boolean metricsAvailable,
    double loadAverage,
    String displayName,
    Instant startedAt,
    Instant lastSeen
) {

}

