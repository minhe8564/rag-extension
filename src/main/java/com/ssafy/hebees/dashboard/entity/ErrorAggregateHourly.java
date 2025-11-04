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
    private Integer systemErrorCount = 0; // 시스템 에러 수

    @Column(name = "RESPONSE_ERROR_COUNT", nullable = false)
    @Builder.Default
    private Integer responseErrorCount = 0; // 응답 에러 수

    @Column(name = "TOTAL_ERROR_COUNT", nullable = false)
    @Builder.Default
    private Integer totalErrorCount = 0; // 총 에러 수
}

