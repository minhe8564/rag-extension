package com.ssafy.hebees.dashboard.dto.request;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.PositiveOrZero;

@Schema(description = "에러 메트릭 증가 요청 DTO")
public record ErrorMetricIncrementRequest(
    @PositiveOrZero
    @Schema(description = "시스템 에러 증가 값", example = "1")
    long systemCount,

    @PositiveOrZero
    @Schema(description = "응답 에러 증가 값", example = "2")
    long responseCount
) {

    public ErrorMetricIncrementRequest {
        if (systemCount <= 0 && responseCount <= 0) {
            throw new IllegalArgumentException("systemCount와 responseCount 중 최소 하나는 양수여야 합니다.");
        }
    }
}

