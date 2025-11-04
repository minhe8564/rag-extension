package com.ssafy.hebees.dashboard.entity;

import com.ssafy.hebees.common.entity.BaseEntity;
import jakarta.persistence.*;

import java.time.LocalDate;
import java.util.UUID;
import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Entity
@Table(
    name = "KEYWORD_AGGREGATE_DAILY",
    uniqueConstraints = {
        @UniqueConstraint(
            name = "UK_KEYWORD_DAILY__AGGREGATE_DATE__KEYWORD",
            columnNames = {"AGGREGATE_DATE", "KEYWORD"}
        )
    }
)
@Getter
@Builder(toBuilder = true)
@AllArgsConstructor(access = AccessLevel.PRIVATE)
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class KeywordAggregateDaily extends BaseEntity {

    @Id
    @Column(name = "AGGREGATE_NO", columnDefinition = "BINARY(16)")
    private UUID aggregateNo; // 집계 ID

    @Column(name = "AGGREGATE_DATE", nullable = false, updatable = false)
    private LocalDate aggregateDate; // 검색일

    @Column(name = "KEYWORD", length = 255, nullable = false, updatable = false)
    private String keyword; // 검색어

    @Column(name = "FREQUENCY", nullable = false)
    @Builder.Default
    private Integer frequency = 0; // 빈도
}

