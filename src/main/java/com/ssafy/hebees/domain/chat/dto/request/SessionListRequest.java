package com.ssafy.hebees.domain.chat.dto.request;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.Size;
import org.springdoc.core.annotations.ParameterObject;

@ParameterObject
@Schema(description = "세션 검색 쿼리 (q만 사용)")
public record SessionListRequest (

        @Schema(description = "검색어(제목 등 부분 일치)", example = "루틴", nullable = true)
        @Size(max = 100, message = "검색어는 100자 이하여야 합니다.")
        String query

) {
    public SessionListRequest {
        // 공백만 들어오면 null로 정규화, 앞뒤 공백 제거
        query = (query == null || query.isBlank()) ? null : query.strip();
    }
}
