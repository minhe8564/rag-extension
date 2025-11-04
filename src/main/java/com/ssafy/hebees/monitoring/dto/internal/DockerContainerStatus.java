package com.ssafy.hebees.monitoring.dto.internal;

/**
 * Docker 컨테이너 상태 정보를 담는 내부 DTO
 */
public record DockerContainerStatus(
    String containerName,
    String rawStatus,
    boolean running
) {

}

