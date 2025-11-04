package com.ssafy.hebees.dashboard.dto.response;

import io.swagger.v3.oas.annotations.media.Schema;
import java.util.List;
import org.springdoc.core.annotations.ParameterObject;

@ParameterObject
@Schema(description = "챗봇 시계열 응답 DTO")
public record ChatbotTimeSeriesResponse(
    @Schema(description = "응답 데이터의 기간 정보")
    Timeframe timeframe,

    @Schema(description = "시계열 데이터 포인트 목록")
    List<TimeseriesPoint<Long>> items
) {

}