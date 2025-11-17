package com.ssafy.hebees.dashboard.service;

import com.ssafy.hebees.chat.client.dto.LlmChatResult;
import com.ssafy.hebees.common.exception.ErrorCode;
import java.util.HashMap;
import java.util.Map;
import java.util.Objects;
import java.util.UUID;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

/**
 * 챗봇 질의/응답 및 오류 정보를 Redis Stream 으로 발행한다.
 *
 * <ul>
 *     <li>generation:history:queries – 사용자 질의</li>
 *     <li>generation:history:metrics – 토큰/응답시간 메트릭</li>
 *     <li>generation:history:errors – 오류 이벤트</li>
 * </ul>
 */
@Slf4j
@Service
public class GenerationHistoryStreamPublisher {

    private static final String QUERY_STREAM_KEY = "generation:history:queries";
    private static final String METRIC_STREAM_KEY = "generation:history:metrics";
    private static final String ERROR_STREAM_KEY = "generation:history:errors";

    private final StringRedisTemplate redisTemplate;

    public GenerationHistoryStreamPublisher(
        @Qualifier("dashboardRedisTemplate") StringRedisTemplate redisTemplate
    ) {
        this.redisTemplate = redisTemplate;
    }

    public void publishQuery(UUID userNo, UUID sessionNo, String query) {
        if (!StringUtils.hasText(query)) {
            return;
        }

        Map<String, String> payload = new HashMap<>();
        payload.put("query", query);
        putIfPresent(payload, "user_id", userNo);
        putIfPresent(payload, "session_id", sessionNo);

        publish(QUERY_STREAM_KEY, payload);
    }

    public void publishMetrics(UUID userNo, UUID sessionNo, UUID llmNo, LlmChatResult result) {
        if (result == null) {
            return;
        }

        Map<String, String> payload = new HashMap<>();
        putIfPresent(payload, "user_id", userNo);
        putIfPresent(payload, "session_id", sessionNo);
        putIfPresent(payload, "llm_no", llmNo);
        putIfPresent(payload, "input_tokens", result.inputTokens());
        putIfPresent(payload, "output_tokens", result.outputTokens());
        putIfPresent(payload, "total_tokens", result.totalTokens());
        putIfPresent(payload, "response_time_ms", result.responseTimeMs());

        publish(METRIC_STREAM_KEY, payload);
    }

    public void publishError(
        UUID userNo,
        UUID sessionNo,
        UUID llmNo,
        String query,
        ErrorCode errorCode,
        Throwable throwable
    ) {
        Map<String, String> payload = new HashMap<>();
        putIfPresent(payload, "user_id", userNo);
        putIfPresent(payload, "session_id", sessionNo);
        putIfPresent(payload, "llm_no", llmNo);
        if (StringUtils.hasText(query)) {
            payload.put("query", query);
        }

        String errorCodeValue = errorCode != null ? errorCode.name() : "UNKNOWN";
        payload.put("error_code", errorCodeValue);
        payload.put("type", resolveErrorType(errorCode));
        payload.put("message", resolveErrorMessage(errorCode, throwable));

        publish(ERROR_STREAM_KEY, payload);
    }

    private void publish(String streamKey, Map<String, String> payload) {
        if (payload.isEmpty()) {
            return;
        }
        try {
            String nonNullStreamKey = Objects.requireNonNull(streamKey, "streamKey must not be null");
            Map<String, String> nonNullPayload = Objects.requireNonNull(payload,
                "payload must not be null");
            redisTemplate.opsForStream().add(nonNullStreamKey, nonNullPayload);
            log.debug("Published Redis stream event. stream={}, payload={}", streamKey, payload);
        } catch (Exception e) {
            log.warn("Failed to publish Redis stream event. stream={}, reason={}",
                streamKey, e.getMessage(), e);
        }
    }

    private String resolveErrorMessage(ErrorCode errorCode, Throwable throwable) {
        if (throwable != null && StringUtils.hasText(throwable.getMessage())) {
            return throwable.getMessage();
        }
        if (errorCode != null && StringUtils.hasText(errorCode.getMessage())) {
            return errorCode.getMessage();
        }
        return "Unknown error";
    }

    private String resolveErrorType(ErrorCode errorCode) {
        if (errorCode == null) {
            return "system";
        }
        HttpStatus status = errorCode.getStatus();
        if (status.is5xxServerError()) {
            return "system";
        }
        return "response";
    }

    private void putIfPresent(Map<String, String> payload, String key, Object value) {
        if (value == null) {
            return;
        }
        if (value instanceof String stringValue) {
            if (StringUtils.hasText(stringValue)) {
                payload.put(key, stringValue);
            }
            return;
        }
        payload.put(key, value.toString());
    }
}

