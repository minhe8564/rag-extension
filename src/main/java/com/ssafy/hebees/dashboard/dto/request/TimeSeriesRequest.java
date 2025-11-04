package com.ssafy.hebees.dashboard.dto.request;

import com.ssafy.hebees.dashboard.dto.Granularity;
import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import org.springdoc.core.annotations.ParameterObject;

@ParameterObject
@Schema(description = "시계열 데이터 요청 DTO")
public record TimeSeriesRequest(
    @NotNull
    @Enumerated(EnumType.STRING)
    @Schema(description = "집계 단위", example = "day", allowableValues = {"day", "week", "month"})
    Granularity granularity,

    @Min(1) @Max(180)
    @Schema(description = "조회 범위(단위 개수)", example = "30")
    Integer scale
) {

    public TimeSeriesRequest {
        if (scale == null) {
            scale = granularity.getDefaultScale();
        }
    }
}
