package com.ssafy.hebees.dashboard.entity;

import com.ssafy.hebees.common.entity.BaseEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.persistence.UniqueConstraint;
import java.time.LocalDateTime;
import java.util.UUID;
import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Entity
@Table(
    name = "MODEL_AGGREGATE_HOURLY",
    uniqueConstraints = {
        @UniqueConstraint(
            name = "UK_MODEL_HOURLY__LLM_NO__AGGREGATE_DATETIME",
            columnNames = {"LLM_NO", "AGGREGATE_DATETIME"}
        )
    }
)
@Getter
@Builder(toBuilder = true)
@AllArgsConstructor(access = AccessLevel.PRIVATE)
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class ModelAggregateHourly extends BaseEntity {

    @Id
    @Column(name = "AGGREGATE_NO", columnDefinition = "BINARY(16)")
    private UUID aggregateNo; // 집계 ID

    @Column(name = "AGGREGATE_DATETIME", nullable = false, updatable = false)
    private LocalDateTime aggregateDateTime; // 집계 시각 (1시간 단위)

    @Column(name = "LLM_NO", columnDefinition = "BINARY(16)", nullable = false, updatable = false)
    private UUID llmNo; // LLM ID

    @Column(name = "INPUT_TOKENS", nullable = false)
    @Builder.Default
    private Long inputTokens = 0L; // 입력 토큰 사용량

    @Column(name = "OUTPUT_TOKENS", nullable = false)
    @Builder.Default
    private Long outputTokens = 0L; // 출력 토큰 사용량

    @Column(name = "TOTAL_TOKENS", nullable = false)
    @Builder.Default
    private Long totalTokens = 0L; // 총 토큰 사용량

    @Column(name = "TOTAL_RESPONSE_TIME_MS", nullable = false)
    @Builder.Default
    private Float totalResponseTimeMs = .0f; // 총 응답 시간 합

    @Column(name = "RESPONSE_COUNT", nullable = false)
    @Builder.Default
    private Long responseCount = 0L; // 응답 횟수

    public void recordUsage(long inputTokenDelta, long outputTokenDelta, long responseTimeMs) {
        inputTokens = safeAdd(inputTokens, inputTokenDelta);
        outputTokens = safeAdd(outputTokens, outputTokenDelta);
        totalTokens = safeSum(inputTokens, outputTokens);
        totalResponseTimeMs = safeFloatAdd(totalResponseTimeMs, Math.max(responseTimeMs, 0L));
        responseCount = safeAdd(responseCount, 1L);
    }

    private long safeAdd(Long base, long delta) {
        long current = base != null ? base : 0L;
        long updated;
        try {
            updated = Math.addExact(current, delta);
        } catch (ArithmeticException e) {
            updated = delta >= 0 ? Long.MAX_VALUE : 0L;
        }
        if (updated < 0L) {
            updated = 0L;
        }
        return updated;
    }

    private long safeSum(long left, long right) {
        long updated;
        try {
            updated = Math.addExact(left, right);
        } catch (ArithmeticException e) {
            updated = Long.MAX_VALUE;
        }
        if (updated < 0L) {
            updated = 0L;
        }
        return updated;
    }

    private float safeFloatAdd(Float base, long delta) {
        float current = base != null ? base : 0F;
        float addition = delta >= 0L ? Math.min(delta, (long) Float.MAX_VALUE) : 0F;
        float updated = current + addition;
        if (Float.isInfinite(updated) || Float.isNaN(updated)) {
            return Float.MAX_VALUE;
        }
        if (updated < 0F) {
            return 0F;
        }
        return updated;
    }
}
