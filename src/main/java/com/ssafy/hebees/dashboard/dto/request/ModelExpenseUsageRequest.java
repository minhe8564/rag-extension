package com.ssafy.hebees.dashboard.dto.request;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.PositiveOrZero;
import java.util.UUID;

@Schema(description = "모델 비용 사용량 갱신 요청")
public record ModelExpenseUsageRequest(
    @NotNull
    @Schema(description = "모델 ID", example = "123e4567-e89b-12d3-a456-426614174000")
    UUID modelNo,

    @PositiveOrZero
    @Schema(description = "증분 입력 토큰 사용량", example = "128")
    long inputTokens,

    @PositiveOrZero
    @Schema(description = "증분 출력 토큰 사용량", example = "64")
    long outputTokens,

    @PositiveOrZero
    @Schema(description = "응답 시간 (ms)", example = "245")
    long responseTimeMs
) {

}


