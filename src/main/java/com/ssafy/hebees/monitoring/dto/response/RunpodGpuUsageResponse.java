// RunpodGpuUsageResponse.java
package com.ssafy.hebees.monitoring.dto.response;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.Min;

@Schema(description = "Runpod GPU 사용률 응답")
public record RunpodGpuUsageResponse(
    @Schema(description = "이벤트 생성 시각 (ISO8601)", example = "2025-11-03T17:55:12+09:00")
    String timestamp,

    @Schema(description = "GPU 인덱스", example = "0")
    @Min(0)
    int gpuIndex,

    @Schema(description = "GPU 이름", example = "NVIDIA GeForce RTX 4090")
    String gpuName,

    @Schema(description = "GPU 사용률 (%)", example = "45.2")
    @DecimalMin(value = "0.0")
    @DecimalMax(value = "100.0")
    double gpuUsagePercent,

    @Schema(description = "GPU 메모리 사용률 (%)", example = "67.8")
    @DecimalMin(value = "0.0")
    @DecimalMax(value = "100.0")
    double memoryUsagePercent,

    @Schema(description = "GPU 메모리 사용량 (MB)", example = "10880")
    @Min(0)
    long memoryUsedMB,

    @Schema(description = "GPU 메모리 총량 (MB)", example = "24564")
    @Min(0)
    long memoryTotalMB,

    @Schema(description = "GPU 온도 (°C)", example = "72")
    @Min(0)
    int temperatureCelsius
) {

}
