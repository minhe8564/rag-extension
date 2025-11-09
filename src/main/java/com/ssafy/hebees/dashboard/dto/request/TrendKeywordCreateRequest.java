package com.ssafy.hebees.dashboard.dto.request;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;

@Schema(name = "TrendKeywordUpdate", description = "트렌드 키워드 등록 요청")
public record TrendKeywordCreateRequest(

    @Schema(description = "사용자 질의", example = "2025 롤드컵의 MVP가 누구인지 알려줘")
    @NotBlank
    String query

) {

    // 입력 정규화(앞뒤 공백 제거, 중복 공백 축소 등)
    public TrendKeywordCreateRequest {
        if (query != null) {
            query = query.trim().replaceAll("\\s{2,}", " ");
        }
    }
}
