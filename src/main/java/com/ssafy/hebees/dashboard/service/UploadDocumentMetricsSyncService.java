package com.ssafy.hebees.dashboard.service;

import java.util.Objects;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.ValueOperations;
import org.springframework.lang.NonNull;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

@Slf4j
@Service
public class UploadDocumentMetricsSyncService {

    private static final String TOTAL_COUNT_KEY = "metrics:uploads:total_count";
    private static final String PROCESSED_COUNT_KEY = "metrics:uploads:processed_count";

    private final DashboardMetricStreamService dashboardMetricStreamService;
    private final StringRedisTemplate redisTemplate;

    public UploadDocumentMetricsSyncService(
        DashboardMetricStreamService dashboardMetricStreamService,
        @Qualifier("dashboardRedisTemplate") StringRedisTemplate redisTemplate
    ) {
        this.dashboardMetricStreamService = dashboardMetricStreamService;
        this.redisTemplate = redisTemplate;
    }

    @SuppressWarnings("DataFlowIssue")
    @Scheduled(fixedDelayString = "${metrics.upload.sync-interval-ms:1000}")
    public void syncUploadedDocumentMetrics() {
        try {
            long totalCount = readLongValue(TOTAL_COUNT_KEY);
            if (totalCount <= 0L) {
                return;
            }

            long processedCount = readLongValue(PROCESSED_COUNT_KEY);
            if (processedCount > totalCount) {
                log.warn("Processed upload count ({}) exceeded total count ({}). Resetting.",
                    processedCount,
                    totalCount);
                ValueOperations<String, String> valueOps =
                    Objects.requireNonNull(redisTemplate.opsForValue());
                String latestTotal = Long.toString(totalCount);
                valueOps.set(Objects.requireNonNull(PROCESSED_COUNT_KEY),
                    Objects.requireNonNull(latestTotal));
                return;
            }

            long delta = totalCount - processedCount;
            if (delta <= 0L) {
                return;
            }

            dashboardMetricStreamService.incrementCurrentUploadDocuments(delta);
            ValueOperations<String, String> valueOps =
                Objects.requireNonNull(redisTemplate.opsForValue());
            String latestTotal = Long.toString(totalCount);
            valueOps.set(Objects.requireNonNull(PROCESSED_COUNT_KEY),
                Objects.requireNonNull(latestTotal));
        } catch (Exception e) {
            log.warn("Failed to synchronize uploaded document metrics from Redis: {}",
                e.getMessage(), e);
        }
    }

    @SuppressWarnings("DataFlowIssue")
    private long readLongValue(@NonNull String key) {
        ValueOperations<String, String> valueOps =
            Objects.requireNonNull(redisTemplate.opsForValue());
        String value = valueOps.get(key);
        if (value == null) {
            return 0L;
        }
        try {
            return Long.parseLong(value);
        } catch (NumberFormatException e) {
            log.warn("Invalid numeric value '{}' for Redis key {}", value, key);
            return 0L;
        }
    }
}

