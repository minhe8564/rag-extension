package com.ssafy.hebees.ingest.service;

import com.ssafy.hebees.common.subscriber.BaseRedisStreamSubscriber;
import com.ssafy.hebees.dashboard.service.DashboardMetricStreamService;
import java.util.Map;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

@Slf4j
@Service
public class FileUploadStreamSubscriber extends BaseRedisStreamSubscriber {

    private static final String STREAM_KEY = "ingest:uploads";
    private static final String GROUP_NAME = "backend-ingest-uploads";

    private final DashboardMetricStreamService dashboardMetricStreamService;

    @Value("${ingest.upload.stream.poll-size:50}")
    private int pollSize;

    @Value("${ingest.upload.stream.block-timeout-ms:1000}")
    private long blockTimeoutMs;

    public FileUploadStreamSubscriber(
        @Qualifier("dashboardRedisTemplate") StringRedisTemplate redisTemplate,
        DashboardMetricStreamService dashboardMetricStreamService
    ) {
        super(redisTemplate, STREAM_KEY, GROUP_NAME, "파일 업로드 스트림");
        this.dashboardMetricStreamService = dashboardMetricStreamService;
    }

    @Scheduled(fixedDelayString = "${ingest.upload.stream.poll-interval-ms:1000}")
    public void pollStream() {
        pollStreamInternal();
    }

    @Override
    protected void handleRecord(Map<String, String> payload) {
        String eventType = payload.getOrDefault("eventType", "");
        if (!"UPLOAD".equalsIgnoreCase(eventType)) {
            log.debug("[UPLOAD] 지원되지 않는 이벤트 유형 수신: {}", eventType);
            return;
        }

        try {
            dashboardMetricStreamService.incrementCurrentUploadDocuments(1L);
        } catch (Exception e) {
            log.warn("[UPLOAD] 업로드 지표 집계 실패: {}", e.getMessage(), e);
        }
    }

    @Override
    protected int getPollSize() {
        return pollSize;
    }

    @Override
    protected long getBlockTimeoutMs() {
        return blockTimeoutMs;
    }
}
