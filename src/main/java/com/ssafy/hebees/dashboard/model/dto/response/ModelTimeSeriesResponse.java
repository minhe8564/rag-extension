package com.ssafy.hebees.dashboard.model.dto.response;

import com.ssafy.hebees.dashboard.dto.response.Timeframe;
import com.ssafy.hebees.dashboard.dto.response.TimeseriesPoint;
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

    @ParameterObject
    @Schema(description = "모델 시계열 데이터")
    public record ModelSeries(
        @Schema(description = "모델 식별자", example = "f4efa376-f839-42e0-a565-33e5fe88800b")
        String modelId,

        @Schema(description = "모델 표시 이름", example = "GPT-4o Mini")
        String modelName,

        @Schema(description = "토큰 사용량 데이터 포인트")
        List<TimeseriesPoint<Long>> usageTokens,

        @Schema(description = "평균 응답 시간(ms) 데이터 포인트")
        List<TimeseriesPoint<Long>> averageResponseTimeMs
    ) {

    }
}

