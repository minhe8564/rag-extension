package com.ssafy.hebees.dashboard.chat.service;

import com.ssafy.hebees.chat.dto.request.MessageErrorCreateRequest;
import com.ssafy.hebees.chat.entity.MessageErrorType;
import com.ssafy.hebees.chat.service.MessageErrorService;
import com.ssafy.hebees.common.subscriber.BaseRedisStreamSubscriber;
import com.ssafy.hebees.dashboard.service.DashboardMetricStreamService;
import java.util.Map;
import java.util.UUID;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

/**
 * Redis Stream(generation:history:errors)을 구독하여 실시간 오류 지표를 갱신한다.
 */
@Slf4j
@Service
public class ErrorStreamSubscriber extends BaseRedisStreamSubscriber {

    private static final String STREAM_KEY = "generation:history:errors";
    private static final String GROUP_NAME = "backend-generation-errors";

    private final DashboardMetricStreamService dashboardMetricStreamService;
    private final MessageErrorService messageErrorService;

    @Value("${metrics.error.stream.poll-size:50}")
    private int pollSize;

    @Value("${metrics.error.stream.block-timeout-ms:1000}")
    private long blockTimeoutMs;

    public ErrorStreamSubscriber(
        @Qualifier("dashboardRedisTemplate") StringRedisTemplate redisTemplate,
        DashboardMetricStreamService dashboardMetricStreamService,
        MessageErrorService messageErrorService
    ) {
        super(redisTemplate, STREAM_KEY, GROUP_NAME, "에러 스트림");
        this.dashboardMetricStreamService = dashboardMetricStreamService;
        this.messageErrorService = messageErrorService;
    }

    @Scheduled(fixedDelayString = "${metrics.error.stream.poll-interval-ms:1000}")
    public void pollStream() {
        pollStreamInternal();
    }

    @Override
    protected void handleRecord(Map<String, String> payload) {
        ErrorEventRecord event = new ErrorEventRecord(
            payload.get("error_code"),
            payload.get("type"),
            payload.get("message"),
            payload.get("user_id"),
            payload.get("session_id"),
            payload.get("llm_no"),
            payload.get("query")
        );
        handleEvent(event);
    }

    @Override
    protected int getPollSize() {
        return pollSize;
    }

    @Override
    protected long getBlockTimeoutMs() {
        return blockTimeoutMs;
    }

    private void handleEvent(ErrorEventRecord event) {
        long systemDelta = determineSystemDelta(event.type());
        long responseDelta = determineResponseDelta(event.type());

        if (systemDelta == 0L && responseDelta == 0L) {
            log.debug("타입 정보가 없어 이벤트를 건너뜁니다: {}", event);
            return;
        }

        try {
            long total = dashboardMetricStreamService.incrementCurrentErrors(
                systemDelta, responseDelta
            );

            messageErrorService.createError(
                new MessageErrorCreateRequest(
                    MessageErrorType.from(event.type),
                    UUID.fromString(event.sessionId),
                    event.message
                )
            );
            log.debug("오류 메트릭 갱신 완료. systemDelta={}, responseDelta={}, total={}",
                systemDelta, responseDelta, total);
        } catch (Exception e) {
            log.warn("오류 메트릭 갱신 실패: {}", e.getMessage(), e);
        }
    }

    private long determineSystemDelta(String type) {
        if (!StringUtils.hasText(type)) {
            return 0L;
        }
        return type.trim().equalsIgnoreCase("system") ? 1L : 0L;
    }

    private long determineResponseDelta(String type) {
        if (!StringUtils.hasText(type)) {
            return 0L;
        }
        return type.trim().equalsIgnoreCase("response") ? 1L : 0L;
    }

    private record ErrorEventRecord(
        String errorCode,
        String type,
        String message,
        String userId,
        String sessionId,
        String llmNo,
        String query
    ) {

    }
}
