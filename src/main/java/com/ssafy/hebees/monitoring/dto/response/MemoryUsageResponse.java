package com.ssafy.hebees.monitoring.dto.response;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.DecimalMin;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Schema(description = "메모리 사용량 응답")
@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class MemoryUsageResponse {

    @Schema(description = "이벤트 생성 시각 (ISO8601)", example = "2025-11-03T18:10:00+09:00")
    private String timestamp;

    @Schema(description = "총 메모리(GB)", example = "32.0")
    @DecimalMin(value = "0.0")
    private double totalMemoryGB;

    @Schema(description = "현재 사용 중 메모리(GB)", example = "8.5")
    @DecimalMin(value = "0.0")
    private double usedMemoryGB;

    @Schema(description = "메모리 사용률(%)", example = "26.6")
    @DecimalMin(value = "0.0")
    private double memoryUsagePercent;
}


