package com.ssafy.hebees.dashboard.dto.response;

import io.swagger.v3.oas.annotations.media.Schema;
import java.time.LocalDate;

@Schema(description = "시계열 데이터 포인트")
public record TimeseriesPoint(
    @Schema(description = "측정 시점", example = "2025-01-15")
    LocalDate x,

    @Schema(description = "측정 값", example = "1234")
    Integer y
) {

}
