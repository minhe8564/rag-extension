package com.ssafy.hebees.chat.dto.request;

import com.ssafy.hebees.chat.dto.request.MessageCreateRequest.ReferencedDocumentCreateRequest;
import com.ssafy.hebees.chat.entity.MessageRole;
import io.swagger.v3.oas.annotations.media.Schema;
import java.util.List;
import java.util.UUID;
import lombok.Builder;

@Schema(description = "메시지 업데이트 요청")
@Builder(toBuilder = true)
public record MessageUpdateRequest(
    @Schema(description = "메시지 유형", nullable = true)
    MessageRole role,

    @Schema(description = "메시지 내용", nullable = true)
    String content,

    @Schema(description = "사용자 ID", nullable = true)
    UUID userNo,

    @Schema(description = "LLM ID", nullable = true)
    UUID llmNo,

    @Schema(description = "입력 토큰 수", nullable = true)
    Long inputTokens,

    @Schema(description = "출력 토큰 수", nullable = true)
    Long outputTokens,

    @Schema(description = "총 토큰 수", nullable = true)
    Long totalTokens,

    @Schema(description = "응답 시간(ms)", nullable = true)
    Long responseTimeMs,

    @Schema(description = "참조 문서 목록", nullable = true)
    List<ReferencedDocumentCreateRequest> references
) {
}

