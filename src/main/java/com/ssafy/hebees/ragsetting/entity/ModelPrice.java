package com.ssafy.hebees.ragsetting.entity;

import com.ssafy.hebees.common.entity.BaseEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.math.BigDecimal;
import java.util.UUID;
import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Entity
@Table(name = "MODEL_PRICE")
@Getter
@Builder(toBuilder = true)
@AllArgsConstructor(access = AccessLevel.PRIVATE)
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class ModelPrice extends BaseEntity {

    @Id
    @Column(name = "LLM_NO", columnDefinition = "BINARY(16)", nullable = false)
    private UUID llmNo;

    @Column(
        name = "INPUT_TOKEN_PRICE_PER_1K_USD",
        precision = 10,
        scale = 6,
        nullable = false
    )
    private BigDecimal inputTokenPricePer1kUsd;

    @Column(
        name = "OUTPUT_TOKEN_PRICE_PER_1K_USD",
        precision = 10,
        scale = 6,
        nullable = false
    )
    private BigDecimal outputTokenPricePer1kUsd;
}
