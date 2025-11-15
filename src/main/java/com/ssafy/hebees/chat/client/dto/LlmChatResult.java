package com.ssafy.hebees.chat.client.dto;

public record LlmChatResult(
    String role,
    String content,
    Long inputTokens,
    Long outputTokens,
    Long totalTokens,
    Long responseTimeMs
) {

    public static LlmChatResult of(String role, String content) {
        return new LlmChatResult(role, content, null, null, null, null);
    }

    public static LlmChatResult ofContent(String content) {
        return of("assistant", content);
    }

    public LlmChatResult withResponseTime(Long responseTimeMs) {
        return new LlmChatResult(role, content, inputTokens, outputTokens, totalTokens, responseTimeMs);
    }
}

