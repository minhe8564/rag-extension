package com.ssafy.hebees.ragsetting.entity;

import com.fasterxml.jackson.databind.JsonNode;
import com.ssafy.hebees.common.entity.BaseEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.Id;
import jakarta.persistence.Index;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.PrePersist;
import jakarta.persistence.Table;
import java.util.UUID;
import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

@Entity
@Table(
    name = "STRATEGY",
    indexes = {
        @Index(name = "IDX_STRATEGY_TYPE_NO", columnList = "STRATEGY_TYPE_NO"),
        @Index(name = "IDX_STRATEGY_NAME", columnList = "NAME"),
        @Index(name = "IDX_STRATEGY_CODE", columnList = "CODE")
    }
)
@Getter
@Builder(toBuilder = true)
@AllArgsConstructor(access = AccessLevel.PRIVATE)
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class Strategy extends BaseEntity {

    @Id
    @Column(name = "STRATEGY_NO", columnDefinition = "BINARY(16)", nullable = false)
    private UUID strategyNo;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "STRATEGY_TYPE_NO", nullable = false)
    private StrategyType strategyType;

    @Column(name = "NAME", length = 50, nullable = false)
    private String name;

    @Column(name = "CODE", length = 255, nullable = false)
    private String code;

    @Column(name = "DESCRIPTION", length = 255, nullable = false)
    private String description;

    @JdbcTypeCode(SqlTypes.JSON)                 // Hibernate 6+ JSON
    @Column(name = "PARAMETER", columnDefinition = "JSON")
    private JsonNode parameter;                  // 자유로운 JSON 구조

    @PrePersist
    private void prePersist() {
        if (strategyNo == null) {
            strategyNo = UUID.randomUUID();
        }
    }

    void setStrategyType(StrategyType strategyType) {
        this.strategyType = strategyType;
    }
}
