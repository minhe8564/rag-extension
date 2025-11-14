package com.ssafy.hebees.chat.dto.response;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.ssafy.hebees.chat.entity.MessageRole;
import io.swagger.v3.oas.annotations.media.Schema;
import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;
import lombok.Builder;

@JsonInclude(JsonInclude.Include.NON_NULL)
@Schema(description = "채팅 메시지 응답")
@Builder(toBuilder = true)
public record MessageResponse(
    @Schema(description = "메시지 ID", format = "uuid")
    UUID messageNo,

    @Schema(description = "메시지 유형", example = "human")
    MessageRole role,

    @Schema(description = "사용자 ID", format = "uuid")
    UUID userNo,

    @Schema(description = "LLM ID", format = "uuid")
    UUID llmNo,

    @Schema(description = "메시지 내용")
    String content,

    @Schema(description = "생성 시각", type = "string", format = "date-time")
    LocalDateTime createdAt,

    @Schema(description = "참조 문서 목록")
    List<ReferencedDocumentResponse> references
) {

}

