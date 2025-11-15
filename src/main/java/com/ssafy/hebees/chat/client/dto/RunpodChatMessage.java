package com.ssafy.hebees.chat.client.dto;

public record RunpodChatMessage(
    String role,
    String content
) {

    public static RunpodChatMessage of(String role, String content) {
        return new RunpodChatMessage(role, content);
    }
}

