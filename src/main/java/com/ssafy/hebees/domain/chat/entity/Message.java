package com.ssafy.hebees.domain.chat.entity;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@Builder(toBuilder = true)
@AllArgsConstructor(access = AccessLevel.PRIVATE)
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class Message {

    private UUID sessionNo; // 세션 ID

    private UUID messageNo; // 메시지 ID

    private MessageRole role; // 메시지 역할

    private String content; // 내용

    private LocalDateTime createdAt; // 생성 시각

    private Long seq; // 커서 페이지용

    private UUID userNo; // 사용자 ID

    private UUID llmNo; // LLM ID

    private Long inputTokens; // 입력 토큰 사용량

    private Long outputTokens; // 출력 토큰 사용량

    private Long totalTokens; // 총 토큰 사용량

    private Long responseTimeMs; // 응답 시간

    @Builder.Default
    private List<MessageReference> referencedDocuments = new ArrayList<>();
}

