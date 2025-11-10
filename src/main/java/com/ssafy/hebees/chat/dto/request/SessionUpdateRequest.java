package com.ssafy.hebees.chat.dto.request;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.Size;

import java.util.UUID;

@Schema(description = "세션 수정 DTO")
public record SessionUpdateRequest(
    @Size(max = 50, message = "제목은 최대 50자까지 입력 가능합니다.")
    @Schema(description = "세션 제목", example = "래그프레스 루틴", maxLength = 50, nullable = true)
    String title,

    @Schema(description = "사용할 LLM 식별자", format = "uuid", example = "123e4567-e89b-12d3-a456-426614174000", nullable = true)
    UUID llm,

    @Schema(description = "사용할 LLM 이름", example = "GPT-4o", nullable = true)
    String llmName
) {

    public SessionUpdateRequest {
        if (title != null) {
            String stripped = title.strip();
            title = stripped.isBlank() ? null : stripped;
        }
    }
}
