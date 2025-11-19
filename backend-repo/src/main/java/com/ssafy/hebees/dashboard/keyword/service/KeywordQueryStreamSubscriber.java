package com.ssafy.hebees.dashboard.keyword.service;

import com.ssafy.hebees.common.subscriber.BaseRedisStreamSubscriber;
import com.ssafy.hebees.dashboard.keyword.dto.request.TrendKeywordRegisterRequest;
import java.util.Map;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

@Slf4j
@Service
public class KeywordQueryStreamSubscriber extends BaseRedisStreamSubscriber {

    private static final String STREAM_KEY = "generation:history:queries";

    private final DashboardKeywordService dashboardKeywordService;

    @Value("${metrics.keyword.stream.poll-size:50}")
    private int pollSize;

    @Value("${metrics.keyword.stream.block-timeout-ms:1000}")
    private long blockTimeoutMs;

    public KeywordQueryStreamSubscriber(
        @Qualifier("dashboardRedisTemplate") StringRedisTemplate redisTemplate,
        DashboardKeywordService dashboardKeywordService
    ) {
        super(redisTemplate, STREAM_KEY, "키워드 스트림");
        this.dashboardKeywordService = dashboardKeywordService;
    }

    @Scheduled(fixedDelayString = "${metrics.keyword.stream.poll-interval-ms:1000}")
    public void pollStream() {
        pollStreamInternal();
    }

    @Override
    protected void handleRecord(Map<String, String> payload) {
        String query = payload.get("query");
        if (!StringUtils.hasText(query)) {
            log.debug("[키워드 스트림] 빈 질의로 인해 이벤트를 건너뜁니다: {}", payload);
            return;
        }

        try {
            dashboardKeywordService.registerKeywords(new TrendKeywordRegisterRequest(query));
        } catch (Exception e) {
            log.warn("[키워드 스트림] 트렌드 키워드 기록 실패: {}", e.getMessage(), e);
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
