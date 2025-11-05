package com.ssafy.hebees.monitoring.dto.response;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.Min;

@Schema(description = "CPU 사용률 응답")
public record CpuUsageResponse(
    @Schema(description = "이벤트 생성 시각 (ISO8601)", example = "2025-11-03T17:55:12+09:00")
    String timestamp,

    @Schema(description = "CPU 사용률 (%)", example = "12.3")
    @DecimalMin(value = "0.0")
    @DecimalMax(value = "100.0")
    double cpuUsagePercent,

    @Schema(description = "총 CPU 코어 수", example = "16")
    @Min(1)
    int totalCores,

    @Schema(description = "현재 사용 중으로 추정되는 코어 수", example = "2")
    @Min(0)
    int activeCores
) {

}


