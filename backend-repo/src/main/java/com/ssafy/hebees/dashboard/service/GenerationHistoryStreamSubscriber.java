package com.ssafy.hebees.dashboard.service;

import com.ssafy.hebees.common.subscriber.BaseRedisStreamSubscriber;
import com.ssafy.hebees.common.util.MonitoringUtils;
import com.ssafy.hebees.dashboard.entity.ChatbotAggregateHourly;
import com.ssafy.hebees.dashboard.model.repository.UsageAggregateHourlyRepository;
import com.ssafy.hebees.dashboard.model.service.AnalyticsExpenseStreamService;
import com.ssafy.hebees.dashboard.model.service.ChatbotUsageStreamService;
import java.time.LocalDateTime;
import java.time.ZonedDateTime;
import java.time.temporal.ChronoUnit;
import java.util.Map;
import java.util.UUID;
import java.util.Objects;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

/**
 * Redis Stream(generation:history:metrics)에 기록된 AI 응답 메타데이터를 구독한다.
 */
@Slf4j
@Service
public class GenerationHistoryStreamSubscriber extends BaseRedisStreamSubscriber {

    private static final String STREAM_KEY = "generation:history:metrics";

    private final AnalyticsExpenseStreamService analyticsExpenseStreamService;
    private final UsageAggregateHourlyRepository usageAggregateHourlyRepository;
    private final ChatbotUsageStreamService chatbotUsageStreamService;

    @Value("${metrics.history.stream.poll-size:20}")
    private int pollSize;

    @Value("${metrics.history.stream.block-timeout-ms:1000}")
    private long blockTimeoutMs;

    public GenerationHistoryStreamSubscriber(
        @Qualifier("dashboardRedisTemplate") StringRedisTemplate redisTemplate,
        AnalyticsExpenseStreamService analyticsExpenseStreamService,
        UsageAggregateHourlyRepository usageAggregateHourlyRepository,
        ChatbotUsageStreamService chatbotUsageStreamService
    ) {
        super(redisTemplate, STREAM_KEY, "히스토리 스트림");
        this.analyticsExpenseStreamService = analyticsExpenseStreamService;
        this.usageAggregateHourlyRepository = usageAggregateHourlyRepository;
        this.chatbotUsageStreamService = chatbotUsageStreamService;
    }

    @Scheduled(fixedDelayString = "${metrics.history.stream.poll-interval-ms:1000}")
    public void pollStream() {
        pollStreamInternal();
    }

    @Override
    protected void handleRecord(Map<String, String> payload) {
        GenerationHistoryMetric metric = GenerationHistoryMetric.from(payload);
        handleMetric(metric);
    }

    @Override
    protected int getPollSize() {
        return pollSize;
    }

    @Override
    protected long getBlockTimeoutMs() {
        return blockTimeoutMs;
    }

    private void handleMetric(GenerationHistoryMetric metric) {
        log.info("[CHAT] Received generation history metric: {}", metric);

        long inputTokens = safeNonNegative(metric.inputTokens());
        long outputTokens = safeNonNegative(metric.outputTokens());
        long totalTokens = safeNonNegative(metric.totalTokens());
        long responseTimeMs = safeNonNegative(metric.responseTimeMs());

        UUID llmNo = parseUuid(metric.llmNo());
        if (llmNo != null) {
            try {
                analyticsExpenseStreamService.recordModelUsage(
                    llmNo,
                    inputTokens,
                    outputTokens,
                    responseTimeMs
                );
            } catch (Exception e) {
                log.warn("[CHAT] Failed to record model usage for llm {}: {}", llmNo,
                    e.getMessage(),
                    e);
            }
        }

        updateChatbotAggregates(inputTokens, outputTokens, responseTimeMs);
        incrementRealtimeChatbotUsage(metric);
    }

    private record GenerationHistoryMetric(
        String userId,
        String sessionId,
        String llmNo,
        Long inputTokens,
        Long outputTokens,
        Long totalTokens,
        Long responseTimeMs
    ) {

        private static GenerationHistoryMetric from(Map<String, String> valueMap) {
            return new GenerationHistoryMetric(
                valueMap.get("user_id"),
                valueMap.get("session_id"),
                valueMap.get("llm_no"),
                toLong(valueMap.get("input_tokens")),
                toLong(valueMap.get("output_tokens")),
                toLong(valueMap.get("total_tokens")),
                toLong(valueMap.get("response_time_ms"))
            );
        }

        private static Long toLong(String candidate) {
            if (candidate == null) {
                return null;
            }
            try {
                return Long.parseLong(candidate);
            } catch (NumberFormatException e) {
                return null;
            }
        }
    }

    private void updateChatbotAggregates(long inputTokens, long outputTokens, long responseTimeMs) {
        LocalDateTime bucket = Objects.requireNonNull(currentHourBucket(), "bucket must not be null");
        try {
            ChatbotAggregateHourly aggregate = usageAggregateHourlyRepository.findById(bucket)
                .orElseGet(() -> ChatbotAggregateHourly.builder()
                    .aggregateDateTime(bucket)
                    .build());

            aggregate.recordUsage(inputTokens, outputTokens, responseTimeMs);
            usageAggregateHourlyRepository.save(aggregate);
        } catch (Exception e) {
            log.warn("[CHAT] Failed to update chatbot aggregate for bucket {}: {}", bucket,
                e.getMessage(), e);
        }
    }

    private void incrementRealtimeChatbotUsage(GenerationHistoryMetric metric) {
        UUID userNo = parseUuid(metric.userId());
        UUID sessionNo = parseUuid(metric.sessionId());
        try {
            if (userNo != null && sessionNo != null) {
                chatbotUsageStreamService.recordChatbotRequest(userNo, sessionNo);
            } else {
                chatbotUsageStreamService.recordChatbotRequests(1L);
            }
        } catch (Exception e) {
            log.warn("[CHAT] Failed to record chatbot request metrics: {}", e.getMessage(), e);
        }
    }

    private UUID parseUuid(String value) {
        if (value == null || value.isBlank()) {
            return null;
        }
        try {
            return UUID.fromString(value.trim());
        } catch (IllegalArgumentException ex) {
            return null;
        }
    }

    private long safeNonNegative(Long candidate) {
        if (candidate == null) {
            return 0L;
        }
        return candidate < 0L ? 0L : candidate;
    }

    private long safeSum(long left, long right) {
        try {
            long sum = Math.addExact(left, right);
            return Math.max(sum, 0L);
        } catch (ArithmeticException e) {
            return Long.MAX_VALUE;
        }
    }

    private LocalDateTime currentHourBucket() {
        return ZonedDateTime.now(MonitoringUtils.KST)
            .truncatedTo(ChronoUnit.HOURS)
            .toLocalDateTime();
    }
}

