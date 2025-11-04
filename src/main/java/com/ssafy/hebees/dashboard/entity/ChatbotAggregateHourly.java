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
@Table(name = "CHATBOT_AGGREGATE_HOURLY")
@Getter
@Builder(toBuilder = true)
@AllArgsConstructor(access = AccessLevel.PRIVATE)
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class ChatbotAggregateHourly extends BaseEntity {

    @Id
    @Column(name = "AGGREGATE_DATETIME")
    private LocalDateTime aggregateDateTime; // 집계 시각(1시간 단위)

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
    private Float totalResponseTimeMs = .0f; // 총 응답 시간 합(ms)

    @Column(name = "RESPONSE_COUNT", nullable = false)
    @Builder.Default
    private Long responseCount = 0L; // 응답 수
}
