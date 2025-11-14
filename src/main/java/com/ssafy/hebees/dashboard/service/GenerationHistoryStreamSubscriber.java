package com.ssafy.hebees.dashboard.service;

import com.ssafy.hebees.common.util.MonitoringUtils;
import com.ssafy.hebees.dashboard.entity.ChatbotAggregateHourly;
import com.ssafy.hebees.dashboard.model.repository.UsageAggregateHourlyRepository;
import com.ssafy.hebees.dashboard.model.service.AnalyticsExpenseStreamService;
import com.ssafy.hebees.dashboard.model.service.ChatbotUsageStreamService;
import jakarta.annotation.PostConstruct;
import java.time.Duration;
import java.time.LocalDateTime;
import java.time.ZonedDateTime;
import java.time.temporal.ChronoUnit;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.UUID;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.dao.DataAccessException;
import org.springframework.data.redis.RedisSystemException;
import org.springframework.data.redis.connection.stream.Consumer;
import org.springframework.data.redis.connection.stream.MapRecord;
import org.springframework.data.redis.connection.stream.ReadOffset;
import org.springframework.data.redis.connection.stream.RecordId;
import org.springframework.data.redis.connection.stream.StreamOffset;
import org.springframework.data.redis.connection.stream.StreamReadOptions;
import org.springframework.data.redis.connection.stream.StreamRecords;
import org.springframework.data.redis.core.StreamOperations;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

/**
 * Redis Stream(generation:history:metrics)에 기록된 AI 응답 메타데이터를 구독한다.
 */
@Slf4j
@Service
public class GenerationHistoryStreamSubscriber {

    private static final String STREAM_KEY = "generation:history:metrics";
    private static final String GROUP_NAME = "backend-generation-history";

    public GenerationHistoryStreamSubscriber(
        @Qualifier("metricsRedisTemplate") StringRedisTemplate redisTemplate,
        AnalyticsExpenseStreamService analyticsExpenseStreamService,
        UsageAggregateHourlyRepository usageAggregateHourlyRepository,
        ChatbotUsageStreamService chatbotUsageStreamService
    ) {
        this.redisTemplate = redisTemplate;
        this.analyticsExpenseStreamService = analyticsExpenseStreamService;
        this.usageAggregateHourlyRepository = usageAggregateHourlyRepository;
        this.chatbotUsageStreamService = chatbotUsageStreamService;
    }

    private final StringRedisTemplate redisTemplate;
    private final AnalyticsExpenseStreamService analyticsExpenseStreamService;
    private final UsageAggregateHourlyRepository usageAggregateHourlyRepository;
    private final ChatbotUsageStreamService chatbotUsageStreamService;

    private String consumerName;

    @Value("${metrics.history.stream.poll-size:20}")
    private int pollSize;

    @Value("${metrics.history.stream.block-timeout-ms:1000}")
    private long blockTimeoutMs;

    @PostConstruct
    void initializeConsumerGroup() {
        consumerName = "consumer-" + UUID.randomUUID();
        ensureConsumerGroup();
    }

    @Scheduled(fixedDelayString = "${metrics.history.stream.poll-interval-ms:1000}")
    public void pollStream() {
        StreamOperations<String, String, String> streamOps =
            Objects.requireNonNull(redisTemplate.opsForStream());

        try {
            List<MapRecord<String, String, String>> records = streamOps.read(
                Consumer.from(GROUP_NAME, consumerName),
                StreamReadOptions.empty()
                    .count(pollSize)
                    .block(Duration.ofMillis(blockTimeoutMs)),
                StreamOffset.create(STREAM_KEY, ReadOffset.lastConsumed())
            );

            if (records == null || records.isEmpty()) {
                return;
            }
            records.forEach(record -> {
                try {
                    GenerationHistoryMetric metric = GenerationHistoryMetric.from(
                        record.getValue());
                    handleMetric(metric);
                    streamOps.acknowledge(STREAM_KEY, GROUP_NAME, record.getId());
                } catch (Exception recordError) {
                    log.warn("[CHAT] Failed to process generation history record {}: {}",
                        record.getId(),
                        recordError.getMessage(), recordError);
                }
            });
        } catch (Exception e) {
            log.warn("[CHAT] Failed to consume generation history metrics from Redis stream: {}",
                e.getMessage(), e);
        }
    }

    private void ensureConsumerGroup() {
        StreamOperations<String, String, String> streamOps =
            Objects.requireNonNull(redisTemplate.opsForStream());
        try {
//            streamOps.createGroup(STREAM_KEY, ReadOffset.latest(), GROUP_NAME);
            streamOps.createGroup(STREAM_KEY, ReadOffset.from("0-0"), GROUP_NAME);
            log.info("[CHAT] Created Redis consumer group '{}' for stream '{}'", GROUP_NAME,
                STREAM_KEY);
        } catch (RedisSystemException e) {
            if (handleCreateGroupException(e, streamOps)) {
                return;
            }
            log.warn("[CHAT] Failed to create consumer group '{}' on stream '{}': {}", GROUP_NAME,
                STREAM_KEY, e.getMessage(), e);
        } catch (DataAccessException e) {
            if (handleCreateGroupException(e, streamOps)) {
                return;
            }
            log.warn("[CHAT] Failed to create consumer group '{}' on stream '{}': {}", GROUP_NAME,
                STREAM_KEY, e.getMessage(), e);
        } catch (Exception e) {
            if (handleCreateGroupException(e, streamOps)) {
                return;
            }
            log.warn("[CHAT] Unexpected error while creating consumer group '{}': {}", GROUP_NAME,
                e.getMessage(), e);
        }
    }

    private void handleMetric(GenerationHistoryMetric metric) {
        log.info("[CHAT] Received generation history metric: {}", metric);

        long inputTokens = safeNonNegative(metric.inputTokens());
        long outputTokens = safeNonNegative(metric.outputTokens());
        long totalTokens = safeNonNegative(metric.totalTokens());
        long responseTimeMs = safeNonNegative(metric.responseTimeMs());

        if (totalTokens == 0L) {
            totalTokens = safeSum(inputTokens, outputTokens);
        }

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
                log.warn("[CHAT] Failed to record model usage for llm {}: {}", llmNo, e.getMessage(),
                    e);
            }
        }

        updateChatbotAggregates(inputTokens, outputTokens, responseTimeMs);
        incrementRealtimeChatbotUsage(metric);
    }

    private boolean handleCreateGroupException(Throwable throwable,
        StreamOperations<String, String, String> streamOps) {
        if (messageContains(throwable, "BUSYGROUP")) {
            log.debug("[CHAT] Redis consumer group '{}' already exists for stream '{}'", GROUP_NAME,
                STREAM_KEY);
            return true;
        }
        if (messageContains(throwable, "ERR no such key")) {
            RecordId bootstrapId = streamOps.add(StreamRecords
                .newRecord()
                .in(STREAM_KEY)
                .ofMap(Collections.singletonMap("bootstrap", "true")));
            streamOps.createGroup(STREAM_KEY, ReadOffset.latest(), GROUP_NAME);
            streamOps.delete(STREAM_KEY, bootstrapId);
            log.info("[CHAT] Initialized stream '{}' and created consumer group '{}'", STREAM_KEY,
                GROUP_NAME);
            return true;
        }
        return false;
    }

    private boolean messageContains(Throwable throwable, String token) {
        Throwable current = throwable;
        while (current != null) {
            String message = current.getMessage();
            if (message != null && message.contains(token)) {
                return true;
            }
            current = current.getCause();
        }
        return false;
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
        LocalDateTime bucket = currentHourBucket();
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
            return sum < 0L ? 0L : sum;
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

