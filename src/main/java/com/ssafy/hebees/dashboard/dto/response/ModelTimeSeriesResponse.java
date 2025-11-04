package com.ssafy.hebees.dashboard.dto.response;

import io.swagger.v3.oas.annotations.media.Schema;
import java.util.List;
import org.springdoc.core.annotations.ParameterObject;

@ParameterObject
@Schema(description = "모델 별 시계열 응답 DTO")
public record ModelTimeSeriesResponse(
    @Schema(description = "응답 데이터의 기간 정보")
    Timeframe timeframe,

    @Schema(description = "모델별 시계열 측정 값 목록")
    List<ModelSeries> model
) {

}

