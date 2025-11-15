package com.ssafy.hebees.dashboard.dto.request;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.Positive;

@Schema(description = "메트릭 증가 요청 DTO")
public record MetricIncrementRequest(
    @Positive
    @Schema(description = "증가시킬 값", example = "5")
    long amount
) {

}

