package com.ssafy.hebees.dashboard.service;

import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

public interface DashboardMetricStreamService {

    SseEmitter subscribeAccessUsers(String lastEventId);

    SseEmitter subscribeUploadDocuments(String lastEventId);

    SseEmitter subscribeErrors(String lastEventId);

    long incrementCurrentAccessUsers(long delta);

    long incrementCurrentUploadDocuments(long delta);

    long incrementCurrentErrors(long systemDelta, long responseDelta);
}
