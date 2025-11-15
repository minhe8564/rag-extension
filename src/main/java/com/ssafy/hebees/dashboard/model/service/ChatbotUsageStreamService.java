package com.ssafy.hebees.dashboard.model.service;

import java.util.UUID;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

public interface ChatbotUsageStreamService {

    void recordChatbotRequest(UUID userNo, UUID sessionNo);

    void recordChatbotRequests(long amount);

    SseEmitter subscribeChatbotStream(String lastEventId);
}

