package com.ssafy.hebees.domain.chat.dto.response;

//import com.fasterxml.jackson.annotation.JsonInclude;
//import com.ssafy.hebees.domain.chat.entity.MessageRole;
//import io.swagger.v3.oas.annotations.media.Schema;
//import java.time.LocalDateTime;
//import java.util.List;
//import java.util.UUID;
//
//@JsonInclude(JsonInclude.Include.NON_NULL)
//@Schema(description = "채팅 메시지 응답")
//public record MessageResponse(
//    @Schema(description = "메시지 ID", format = "uuid")
//    UUID messageNo,
//
//    @Schema(description = "메시지 유형", example = "human")
//    MessageRole role,
//
//    @Schema(description = "사용자 ID", format = "uuid")
//    UUID userNo,
//
//    @Schema(description = "LLM ID", format = "uuid")
//    UUID llmNo,
//
//    @Schema(description = "메시지 내용")
//    String content,
//
//    @Schema(description = "생성 시각", type = "string", format = "date-time")
//    LocalDateTime createdAt,
//
//    @Schema(description = "세션 내 순번")
//    Long seq,
//
//    @Schema(description = "입력 토큰 수")
//    Long inputTokens,
//
//    @Schema(description = "출력 토큰 수")
//    Long outputTokens,
//
//    @Schema(description = "총 토큰 수")
//    Long totalTokens,
//
//    @Schema(description = "응답 시간(ms)")
//    Long responseTimeMs,
//
//    @Schema(description = "참조 문서 목록")
//    List<ReferencedDocumentResponse> referencedDocuments
//) {
//
//}

