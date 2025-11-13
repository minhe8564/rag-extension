package com.ssafy.hebees.dashboard.dto.request;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import org.springdoc.core.annotations.ParameterObject;

@ParameterObject
@Schema(description = "트랜드 키워드 목록 요청 DTO")
public record TrendKeywordRequest(
    @Schema(description = "분석 기간(일)", example = "7", defaultValue = "7")
    @Min(1) @Max(31)
    Integer scale,

    @Schema(description = "상위 키워드 개수", example = "50", defaultValue = "50")
    @Min(1) @Max(100)
    Integer topK
) {

    public static final int DEFAULT_SCALE = 7;
    public static final int DEFAULT_TOP_K = 50;

    public TrendKeywordRequest {
        if (scale == null) {
            scale = DEFAULT_SCALE;
        }
        if (topK == null) {
            topK = DEFAULT_TOP_K;
        }
    }
}
