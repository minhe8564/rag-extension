package com.ssafy.hebees.chat.dto.request;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.Size;

import java.util.UUID;

@Schema(description = "세션 생성 DTO")
public record SessionCreateRequest(
        @Size(min = 1, max = 50, message = "제목은 1~50자여야 합니다.")
        @Schema(description = "세션 제목", example = "래그프레스 루틴", minLength = 1, maxLength = 50, nullable = true, defaultValue = "새 채팅")
        String title,

        @Schema(description = "사용할 LLM 식별자", format = "uuid", example = "123e4567-e89b-12d3-a456-426614174000", nullable = true)
        UUID llm
) {
    public static final String DEFAULT_TITLE = "새 채팅";

    public SessionCreateRequest {
        if (title == null || title.isBlank()) {
            title = DEFAULT_TITLE;
        } else {
            title = title.strip();
        }
    }
}



