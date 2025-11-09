package com.ssafy.hebees.dashboard.dto.response;

import io.swagger.v3.oas.annotations.media.Schema;
import java.util.List;

@Schema(description = "트렌드 키워드 등록 응답 DTO")
public record TrendKeywordCreateResponse(
    List<String> keywords
) {

    public static TrendKeywordCreateResponse of(List<String> keywords) {
        return new TrendKeywordCreateResponse(keywords);
    }
}
