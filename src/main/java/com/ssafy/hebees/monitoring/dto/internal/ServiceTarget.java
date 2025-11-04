package com.ssafy.hebees.monitoring.dto.internal;

/**
 * 모니터링 대상 서비스 정보를 담는 내부 DTO
 */
public record ServiceTarget(
    String serviceName,
    String containerName
) {

}

