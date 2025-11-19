package com.ssafy.hebees.chat.client.dto;

import java.util.List;

public record RunpodChatRequest(
    String model,
    List<RunpodChatMessage> messages,
    boolean stream
) {

    public static RunpodChatRequest of(String model, List<RunpodChatMessage> messages) {
        return new RunpodChatRequest(model, messages, false);
    }
}
