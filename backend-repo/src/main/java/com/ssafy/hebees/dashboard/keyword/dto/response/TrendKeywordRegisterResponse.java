package com.ssafy.hebees.dashboard.keyword.dto.response;

import io.swagger.v3.oas.annotations.media.Schema;
import java.util.List;

@Schema(description = "트렌드 키워드 등록 응답 DTO")
public record TrendKeywordRegisterResponse(
    List<String> keywords
) {

}
