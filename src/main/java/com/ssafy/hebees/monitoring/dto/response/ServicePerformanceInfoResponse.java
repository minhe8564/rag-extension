package com.ssafy.hebees.monitoring.dto.response;

import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "서비스별 성능 정보")
public record ServicePerformanceInfoResponse(
    @Schema(description = "서비스 이름", example = "chunking-repo")
    String serviceName,

    @Schema(description = "1분 Load Average", example = "0.82")
    double loadAvg1m,

    @Schema(description = "CPU 사용률(%)", example = "62.5")
    double cpuUsagePercent,

    @Schema(description = "메모리 사용률(%)", example = "55.3")
    double memoryUsagePercent,

    @Schema(description = "CPU/메모리 합산 점수 (%)", example = "59.01")
    double compositeScore,

    @Schema(description = "서비스 상태", example = "NORMAL")
    String status
) {

}
