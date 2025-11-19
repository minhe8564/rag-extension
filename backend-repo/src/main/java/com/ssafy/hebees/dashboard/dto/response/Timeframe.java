package com.ssafy.hebees.dashboard.dto.response;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonInclude.Include;
import io.swagger.v3.oas.annotations.media.Schema;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.LocalTime;

@JsonInclude(Include.NON_NULL)
@Schema(description = "시계열 범위 정보")
public record Timeframe(
    @Schema(description = "시작 시각", example = "2025-01-01T00:00:00")
    LocalDateTime start,

    @Schema(description = "종료 시각", example = "2025-01-31T23:59:59.999999999")
    LocalDateTime end,

    @Schema(description = "집계 간격", example = "day")
    String granularity
) {

    public Timeframe(LocalDateTime start, LocalDateTime end) {
        this(start, end, null);
    }

    public Timeframe(LocalDate start, LocalDate end) {
        this(start, end, null);
    }

    public Timeframe(LocalDate start, LocalDate end, String granularity) {
        this(
            start != null ? start.atStartOfDay() : null,
            end != null ? end.atTime(LocalTime.MAX) : null,
            granularity
        );
    }

    public Timeframe {
        if (start != null && end != null && end.isBefore(start)) {
            throw new IllegalArgumentException("end는 start보다 같거나 이후여야 합니다.");
        }
    }
}
