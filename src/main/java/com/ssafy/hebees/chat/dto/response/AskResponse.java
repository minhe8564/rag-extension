package com.ssafy.hebees.chat.dto.response;

import io.swagger.v3.oas.annotations.media.Schema;
import java.time.LocalDateTime;
import java.util.UUID;

@Schema(description = "질문 응답 DTO")
public record AskResponse(
    @Schema(description = "생성된 메시지 식별자", example = "2f1b9af4-3e6d-4a2c-8b7a-123456789abc", format = "uuid")
    UUID messageNo,
    @Schema(description = "메시지 역할", example = "ai")
    String role,
    @Schema(description = "LLM이 반환한 응답 본문", example = "안녕하세요! 무엇을 도와드릴까요?")
    String content,
    @Schema(description = "응답이 생성된 시각")
    LocalDateTime createdAt
) {

}
