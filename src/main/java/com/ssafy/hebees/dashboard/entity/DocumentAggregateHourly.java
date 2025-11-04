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
@Table(name = "DOCUMENT_AGGREGATE_HOURLY")
@Getter
@Builder(toBuilder = true)
@AllArgsConstructor(access = AccessLevel.PRIVATE)
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class DocumentAggregateHourly extends BaseEntity {

    @Id
    @Column(name = "AGGREGATE_DATETIME")
    private LocalDateTime aggregateDatetime; // 집계 시각 (1시간 단위)

    @Column(name = "UPLOAD_COUNT", nullable = false)
    @Builder.Default
    private Long uploadCount = 0L; // 업로드 수
}
