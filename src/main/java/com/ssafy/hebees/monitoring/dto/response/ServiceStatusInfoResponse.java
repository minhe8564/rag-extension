package com.ssafy.hebees.monitoring.dto.response;

import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "서비스 실행 상태 정보")
public record ServiceStatusInfoResponse(
    @Schema(description = "서비스 이름", example = "chunking-repo")
    String serviceName,

    @Schema(description = "실행 상태", example = "RUNNING")
    String status,

    @Schema(description = "서비스 시작 시각 (ISO8601)", example = "2025-11-03T11:20:10+09:00")
    String startedAt,

    @Schema(description = "가동 시간 (사람이 읽기 쉬운 형식)", example = "2d 37m")
    String uptimeSeconds
) {

    public enum Status {
        RUNNING,
        STOPPED,
        UNKNOWN
    }
}
