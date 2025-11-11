package com.ssafy.hebees.dashboard.service;

import com.ssafy.hebees.dashboard.dto.response.ModelPriceResponse;
import java.util.UUID;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

public interface AnalyticsExpenseStreamService {

    SseEmitter subscribeExpenseStream(String lastEventId);

    ModelPriceResponse recordModelUsage(UUID modelId, long inputTokens, long outputTokens,
        long responseTimeMs);

    void notifyExpenseChanged();
}

