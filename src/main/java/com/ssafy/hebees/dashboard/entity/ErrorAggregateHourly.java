package com.ssafy.hebees.dashboard.entity;

import com.ssafy.hebees.common.entity.BaseEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.time.LocalDateTime;

import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Entity
@Table(name = "ERROR_AGGREGATE_HOURLY")
@Getter
@Builder(toBuilder = true)
@AllArgsConstructor(access = AccessLevel.PRIVATE)
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class ErrorAggregateHourly extends BaseEntity {

    @Id
    @Column(name = "ERROR_AGGREGATE_DATETIME")
    private LocalDateTime errorAggregateDatetime; // 집계 시각 (1시간 단위)

    @Column(name = "SYSTEM_ERROR_COUNT", nullable = false)
    @Builder.Default
    private Long systemErrorCount = 0L; // 시스템 에러 수

    @Column(name = "RESPONSE_ERROR_COUNT", nullable = false)
    @Builder.Default
    private Long responseErrorCount = 0L; // 응답 에러 수

    @Column(name = "TOTAL_ERROR_COUNT", nullable = false)
    @Builder.Default
    private Long totalErrorCount = 0L; // 총 에러 수

    public long increaseErrorCounts(long systemDelta, long responseDelta) {
        systemErrorCount = applyDelta(systemErrorCount, systemDelta);
        responseErrorCount = applyDelta(responseErrorCount, responseDelta);
        totalErrorCount = recomputeTotal(systemErrorCount, responseErrorCount);
        return totalErrorCount;
    }

    private long applyDelta(Long current, long delta) {
        long base = current != null ? current : 0L;
        long updated;
        try {
            updated = Math.addExact(base, delta);
        } catch (ArithmeticException e) {
            updated = delta > 0 ? Long.MAX_VALUE : 0L;
        }
        if (updated < 0L) {
            updated = 0L;
        }
        return updated;
    }

    private long recomputeTotal(Long system, Long response) {
        long systemValue = system != null ? system : 0L;
        long responseValue = response != null ? response : 0L;
        long total;
        try {
            total = Math.addExact(systemValue, responseValue);
        } catch (ArithmeticException e) {
            total = Long.MAX_VALUE;
        }
        return Math.max(total, 0L);
    }
}
