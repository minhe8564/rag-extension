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

    @Column(name = "LLM_NAME", length = 255, nullable = false, updatable = false)
    private String llmName; // LLM 이름

    @Column(name = "INPUT_TOKENS", nullable = false)
    @Builder.Default
    private Integer inputTokens = 0; // 입력 토큰 사용량

    @Column(name = "OUTPUT_TOKENS", nullable = false)
    @Builder.Default
    private Integer outputTokens = 0; // 출력 토큰 사용량

    @Column(name = "TOTAL_TOKENS", nullable = false)
    @Builder.Default
    private Integer totalTokens = 0; // 총 토큰 사용량

    @Column(name = "TOTAL_RESPONSE_TIME_MS", nullable = false)
    @Builder.Default
    private Float totalResponseTimeMs = .0f; // 총 응답 시간 합

    @Column(name = "RESPONSE_COUNT", nullable = false)
    @Builder.Default
    private Integer responseCount = 0; // 응답 횟수
}

