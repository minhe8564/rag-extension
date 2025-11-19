package com.ssafy.hebees.dashboard.model.service;

import com.ssafy.hebees.dashboard.dto.request.ChatbotRandomConfigRequest;
import com.ssafy.hebees.dashboard.dto.response.ChatbotRandomConfigResponse;
import java.util.UUID;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

public interface ChatbotUsageStreamService {

    void recordChatbotRequest(UUID userNo, UUID sessionNo);

    void recordChatbotRequests(long amount);

    SseEmitter subscribeChatbotStream(String lastEventId);

    ChatbotRandomConfigResponse setRandomConfig(ChatbotRandomConfigRequest request);

    ChatbotRandomConfigResponse getRandomConfig();
}

