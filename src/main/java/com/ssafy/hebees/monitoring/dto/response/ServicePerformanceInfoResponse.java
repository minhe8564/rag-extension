package com.ssafy.hebees.monitoring.dto.response;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Schema(description = "서비스별 성능 정보")
@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ServicePerformanceInfoResponse {

    @Schema(description = "서비스 이름", example = "chunking-repo")
    private String serviceName;

    @Schema(description = "1분 Load Average", example = "0.82")
    private double loadAvg1m;

    @Schema(description = "CPU 사용률 (%)", example = "62.5")
    private double cpuUsagePercent;

    @Schema(description = "메모리 사용률 (%)", example = "55.3")
    private double memoryUsagePercent;

    @Schema(description = "CPU/메모리 통합 점수 (%)", example = "59.01")
    private double compositeScore;

    @Schema(description = "서비스 상태", example = "NORMAL")
    private String status;
}
