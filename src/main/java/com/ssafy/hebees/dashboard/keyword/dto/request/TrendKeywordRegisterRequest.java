package com.ssafy.hebees.dashboard.keyword.dto.request;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;

@Schema(name = "TrendKeywordUpdate", description = "트렌드 키워드 등록 요청")
public record TrendKeywordRegisterRequest(

    @Schema(description = "사용자 질의", example = "2025 롤드컵의 MVP가 누구인지 알려줘")
    @NotBlank
    String query

) {

}
