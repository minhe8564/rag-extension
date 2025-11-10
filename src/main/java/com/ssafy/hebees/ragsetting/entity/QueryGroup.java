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
    name = "QUERY_GROUP",
    indexes = {
        @Index(name = "IDX_QUERY_GROUP_NAME", columnList = "NAME"),
        @Index(name = "IDX_QUERY_GROUP_TRANSFORMATION", columnList = "TRANSFORMATION_STRATEGY_NO"),
        @Index(name = "IDX_QUERY_GROUP_RETRIEVAL", columnList = "RETRIEVAL_STRATEGY_NO"),
        @Index(name = "IDX_QUERY_GROUP_RERANKING", columnList = "RERANKING_STRATEGY_NO"),
        @Index(name = "IDX_QUERY_GROUP_SYSTEM_PROMPTING", columnList = "SYSTEM_PROMPTING_STRATEGY_NO"),
        @Index(name = "IDX_QUERY_GROUP_USER_PROMPTING", columnList = "USER_PROMPTING_STRATEGY_NO"),
        @Index(name = "IDX_QUERY_GROUP_GENERATION", columnList = "GENERATION_STRATEGY_NO")
    }
)
@Getter
@Builder(toBuilder = true)
@AllArgsConstructor(access = AccessLevel.PRIVATE)
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class QueryGroup extends BaseEntity {

    @Id
    @Column(name = "QUERY_GROUP_NO", columnDefinition = "BINARY(16)", nullable = false)
    private UUID queryGroupNo;

    @Column(name = "NAME", length = 100, nullable = false)
    private String name;

    @Column(name = "IS_DEFAULT", nullable = false)
    private boolean isDefault;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "TRANSFORMATION_STRATEGY_NO", nullable = false)
    private Strategy transformationStrategy;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "RETRIEVAL_STRATEGY_NO", nullable = false)
    private Strategy retrievalStrategy;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "RERANKING_STRATEGY_NO", nullable = false)
    private Strategy rerankingStrategy;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "SYSTEM_PROMPTING_STRATEGY_NO", nullable = false)
    private Strategy systemPromptingStrategy;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "USER_PROMPTING_STRATEGY_NO", nullable = false)
    private Strategy userPromptingStrategy;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "GENERATION_STRATEGY_NO", nullable = false)
    private Strategy generationStrategy;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "TRANSFORMATION_PARAMETER", columnDefinition = "JSON", nullable = false)
    private JsonNode transformationParameter;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "RETRIEVAL_PARAMETER", columnDefinition = "JSON", nullable = false)
    private JsonNode retrievalParameter;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "RERANKING_PARAMETER", columnDefinition = "JSON", nullable = false)
    private JsonNode rerankingParameter;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "SYSTEM_PROMPTING_PARAMETER", columnDefinition = "JSON", nullable = false)
    private JsonNode systemPromptingParameter;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "USER_PROMPTING_PARAMETER", columnDefinition = "JSON", nullable = false)
    private JsonNode userPromptingParameter;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "GENERATION_PARAMETER", columnDefinition = "JSON", nullable = false)
    private JsonNode generationParameter;

    @PrePersist
    private void prePersist() {
        if (queryGroupNo == null) {
            queryGroupNo = UUID.randomUUID();
        }
    }
}

