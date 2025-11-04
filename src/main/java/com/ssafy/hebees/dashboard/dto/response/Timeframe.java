package com.ssafy.hebees.dashboard.dto.response;

import io.swagger.v3.oas.annotations.media.Schema;
import java.time.LocalDate;

@Schema(description = "시계열 범위 정보")
public record Timeframe(
    @Schema(description = "시작 일자", example = "2025-01-01")
    LocalDate start,

    @Schema(description = "종료 일자", example = "2025-01-31")
    LocalDate end,

    @Schema(description = "집계 간격", example = "day")
    String granularity
) {

}
