package com.ssafy.hebees.chat.dto.request;

import com.ssafy.hebees.chat.entity.MessageRole;
import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotNull;
import java.util.List;
import java.util.UUID;

@Schema(description = "메시지 생성 요청")
public record MessageCreateRequest(
    @NotNull(message = "메시지 유형은 필수입니다.")
    @Schema(description = "메시지 유형", requiredMode = Schema.RequiredMode.REQUIRED)
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

    @Valid
    @Schema(description = "참조 문서 목록", nullable = true)
    List<ReferencedDocumentCreateRequest> references
) {

    @Schema(description = "참조 문서 생성 요청")
    public record ReferencedDocumentCreateRequest(
        @Schema(description = "파일 ID", nullable = true)
        UUID fileNo,

        @Schema(description = "파일명", nullable = true)
        String name,

        @Schema(description = "파일 제목", nullable = true)
        String title,

        @Schema(description = "파일 확장자", nullable = true)
        String type,

        @Schema(description = "페이지 인덱스", nullable = true)
        Integer index,

        @Schema(description = "다운로드 URL", nullable = true)
        String downloadUrl,

        @Schema(description = "요약/발췌", nullable = true)
        String snippet
    ) {
    }
}

