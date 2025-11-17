package com.ssafy.hebees.chat.client.dto;

import com.fasterxml.jackson.databind.JsonNode;
import com.ssafy.hebees.chat.client.LlmProvider;
import java.util.List;

public record LlmChatRequest(
    LlmProvider provider,
    String model,
    String apiKey,
    List<LlmChatMessage> messages,
    JsonNode parameter,
    String strategyName,
    String strategyCode
) {

}

