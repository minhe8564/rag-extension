package com.ssafy.hebees.monitoring.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.ssafy.hebees.monitoring.dto.response.MetricResponse;
import com.ssafy.hebees.monitoring.dto.response.MetricsListResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.ZSetOperations;
import org.springframework.stereotype.Service;

import jakarta.annotation.PostConstruct;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;
import java.util.Properties;
import org.springframework.data.redis.connection.lettuce.LettuceConnectionFactory;
import org.springframework.data.redis.connection.RedisStandaloneConfiguration;

/**
 * RAG Pipeline 메트릭 조회 서비스 Redis DB 4에서 메트릭 데이터를 조회하여 평균 응답시간 계산
 */
@Slf4j
@Service
public class RagMetricsService {

    private static final int DEFAULT_WINDOW_SECONDS = 300; // 기본 5분
    private static final String[] METRIC_KEYS = {
        "extract:metrics:response_time",
        "chunking:metrics:response_time",
        "embedding:metrics:response_time",
        "query_embedding:metrics:response_time",
        "search:metrics:response_time",
        "cross_encoder:metrics:response_time",
        "generation:metrics:response_time"
    };

    private final StringRedisTemplate metricsRedisTemplate;
    private final ObjectMapper objectMapper = new ObjectMapper();

    public RagMetricsService(
        @Qualifier("metricsRedisTemplate") StringRedisTemplate metricsRedisTemplate) {
        this.metricsRedisTemplate = metricsRedisTemplate;
    }

    /**
     * 모든 메트릭의 평균 응답시간 조회
     *
     * @param windowSeconds 조회할 시간 범위 (초), null이면 기본값(5분) 사용
     * @return 메트릭 목록
     */
    public MetricsListResponse getAllMetrics(Integer windowSeconds) {
        int window = windowSeconds != null ? windowSeconds : DEFAULT_WINDOW_SECONDS;
        List<MetricResponse> metrics = new ArrayList<>();

        for (String metricKey : METRIC_KEYS) {
            try {
                MetricResponse metric = getAverageResponseTime(metricKey, window);
                metrics.add(metric);
            } catch (Exception e) {
                log.error("Failed to get metric for key: {}", metricKey, e);
                // 에러 발생 시 빈 메트릭 추가
                metrics.add(MetricResponse.builder()
                    .name(getDisplayName(metricKey))
                    .averageTimeMs(0.0)
                    .count(0)
                    .minTimeMs(0.0)
                    .maxTimeMs(0.0)
                    .build());
            }
        }

        return new MetricsListResponse(metrics);
    }

    /**
     * 특정 메트릭 키의 평균 응답시간 계산
     *
     * @param metricKey     Redis 키
     * @param windowSeconds 조회할 시간 범위 (초)
     * @return 메트릭 응답
     */
    public MetricResponse getAverageResponseTime(String metricKey, int windowSeconds) {
        try {
            ZSetOperations<String, String> zSetOps = metricsRedisTemplate.opsForZSet();

            Boolean exists = metricsRedisTemplate.hasKey(metricKey);
            log.info("Redis key '{}' exists: {}", metricKey, exists);

            if (Boolean.FALSE.equals(exists)) {
                log.warn("Redis key '{}' does not exist", metricKey);
                return MetricResponse.builder()
                    .name(getDisplayName(metricKey))
                    .averageTimeMs(0.0)
                    .count(0)
                    .minTimeMs(0.0)
                    .maxTimeMs(0.0)
                    .build();
            }

            Long totalCount = zSetOps.count(metricKey, Double.NEGATIVE_INFINITY,
                Double.POSITIVE_INFINITY);
            log.info("Redis key '{}' total count: {}", metricKey, totalCount);

            // 현재 시간을 초 단위 double로 계산 (Python time.time()과 동일한 형식)
            double currentTime = System.currentTimeMillis() / 1000.0;
            double startTime = currentTime - windowSeconds;

            log.info("Querying Redis key: {}, startTime: {}, currentTime: {}, window: {}s",
                metricKey, startTime, currentTime, windowSeconds);

            // Sorted Set에서 시간 범위 내 데이터 조회
            Set<String> members = zSetOps.rangeByScore(
                metricKey,
                startTime,
                currentTime
            );

            log.info("Found {} members for key: {} in range [{}, {}]",
                members != null ? members.size() : 0, metricKey, startTime, currentTime);

            // 시간 범위 내에 데이터가 없으면 0 반환
            if (members == null || members.isEmpty()) {
                log.info(
                    "No members found in time range [{} - {}] for key: {}. Returning empty metrics.",
                    startTime, currentTime, metricKey);
                return MetricResponse.builder()
                    .name(getDisplayName(metricKey))
                    .averageTimeMs(0.0)
                    .count(0)
                    .minTimeMs(0.0)
                    .maxTimeMs(0.0)
                    .build();
            }

            // JSON 파싱 및 time_ms 추출
            List<Double> timesMs = new ArrayList<>();
            for (String member : members) {
                try {
                    JsonNode jsonNode = objectMapper.readTree(member);
                    JsonNode timeMsNode = jsonNode.get("time_ms");
                    if (timeMsNode != null && timeMsNode.isNumber()) {
                        timesMs.add(timeMsNode.asDouble());
                    }
                } catch (Exception e) {
                    log.warn("Failed to parse metric data: {}, error: {}", member, e.getMessage());
                }
            }

            if (timesMs.isEmpty()) {
                log.warn("No valid time_ms found in members for key: {}", metricKey);
                return MetricResponse.builder()
                    .name(getDisplayName(metricKey))
                    .averageTimeMs(0.0)
                    .count(0)
                    .minTimeMs(0.0)
                    .maxTimeMs(0.0)
                    .build();
            }

            // 통계 계산
            double sum = timesMs.stream().mapToDouble(Double::doubleValue).sum();
            double average = sum / timesMs.size();
            double minTime = timesMs.stream().mapToDouble(Double::doubleValue).min().orElse(0.0);
            double maxTime = timesMs.stream().mapToDouble(Double::doubleValue).max().orElse(0.0);

            log.info("Calculated metrics for key: {}, count: {}, average: {}ms",
                metricKey, timesMs.size(), average);

            return MetricResponse.builder()
                .name(getDisplayName(metricKey))
                .averageTimeMs(Math.round(average * 100.0) / 100.0) // 소수점 2자리
                .count(timesMs.size())
                .minTimeMs(Math.round(minTime * 100.0) / 100.0)
                .maxTimeMs(Math.round(maxTime * 100.0) / 100.0)
                .build();

        } catch (Exception e) {
            log.error("Error calculating average response time for key: {}", metricKey, e);
            throw new RuntimeException("Failed to calculate metrics", e);
        }
    }

    /**
     * 메트릭 키에 대한 표시 이름 반환
     */
    private String getDisplayName(String metricKey) {
        return switch (metricKey) {
            case "extract:metrics:response_time" -> "Extract";
            case "chunking:metrics:response_time" -> "Chunking";
            case "embedding:metrics:response_time" -> "Embedding";
            case "query_embedding:metrics:response_time" -> "Query Embedding";
            case "search:metrics:response_time" -> "Search";
            case "cross_encoder:metrics:response_time" -> "Cross Encoder";
            case "generation:metrics:response_time" -> "Generation";
            default -> metricKey;
        };
    }
}
