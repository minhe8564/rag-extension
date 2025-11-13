package com.ssafy.hebees.dashboard.model.service;

import com.ssafy.hebees.dashboard.dto.request.TimeSeriesRequest;
import com.ssafy.hebees.dashboard.model.dto.response.ChatbotTimeSeriesResponse;
 import com.ssafy.hebees.dashboard.model.dto.response.HeatmapResponse;
 import com.ssafy.hebees.dashboard.model.dto.response.ModelTimeSeriesResponse;
import com.ssafy.hebees.dashboard.dto.request.ModelExpenseUsageRequest;
import com.ssafy.hebees.dashboard.dto.response.ModelPriceResponse;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

public interface DashboardModelService {

    ChatbotTimeSeriesResponse getChatbotTimeSeries(TimeSeriesRequest request);

    ModelTimeSeriesResponse getModelTimeSeries(TimeSeriesRequest request);

    HeatmapResponse getChatbotHeatmap();

    SseEmitter subscribeChatbotStream(String lastEventId);

    SseEmitter subscribeExpenseStream(String lastEventId);

    void incrementChatbotRequests(long amount);

    ModelPriceResponse recordExpenseUsage(ModelExpenseUsageRequest request);
}


