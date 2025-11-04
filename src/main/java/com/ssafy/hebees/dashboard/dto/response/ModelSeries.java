package com.ssafy.hebees.dashboard.dto.response;

import io.swagger.v3.oas.annotations.media.Schema;
import java.util.List;
import org.springdoc.core.annotations.ParameterObject;

@ParameterObject
@Schema(description = "모델 시계열 데이터")
public record ModelSeries(
    @Schema(description = "모델 식별자", example = "gpt-4o-mini")
    String modelId,

    @Schema(description = "모델 표시 이름", example = "GPT-4o Mini")
    String modelName,

    @Schema(description = "토큰 사용량 데이터 포인트")
    List<TimeseriesPoint> usageTokens,

    @Schema(description = "평균 응답 시간(ms) 데이터 포인트")
    List<TimeseriesPoint> averageResponseTimeMs
) {

}

