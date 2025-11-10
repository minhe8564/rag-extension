package com.ssafy.hebees.dashboard.service;

import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

public interface AnalyticsExpenseStreamService {

    SseEmitter subscribeExpenseStream(String lastEventId);

    void notifyExpenseChanged();
}

