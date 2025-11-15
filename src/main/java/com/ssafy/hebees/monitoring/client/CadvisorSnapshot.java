package com.ssafy.hebees.monitoring.client;

import java.util.List;

/**
 * cAdvisor 스냅샷 (컨테이너 메트릭 목록)
 */
public record CadvisorSnapshot(
    List<CadvisorContainerMetrics> containers,
    long machineMemoryBytes
) {

    public static CadvisorSnapshot empty(long memoryBytes) {
        return new CadvisorSnapshot(List.of(), memoryBytes);
    }
}

