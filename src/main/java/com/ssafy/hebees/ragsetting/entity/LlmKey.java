package com.ssafy.hebees.ragsetting.entity;

import com.ssafy.hebees.user.entity.User;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.Id;
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

@Entity
@Table(name = "LLM_KEY")
@Getter
@Builder(toBuilder = true)
@AllArgsConstructor(access = AccessLevel.PRIVATE)
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class LlmKey {

    @Id
    @Column(name = "LLM_KEY_NO", columnDefinition = "BINARY(16)", nullable = false)
    private UUID llmKeyNo;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(
        name = "USER_NO",
        referencedColumnName = "USER_NO",
        nullable = false,
        columnDefinition = "BINARY(16)"
    )
    private User user;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(
        name = "STRATEGY_NO",
        referencedColumnName = "STRATEGY_NO",
        nullable = false,
        columnDefinition = "BINARY(16)"
    )
    private Strategy strategy;

    @Column(name = "API_KEY", nullable = false)
    private String apiKey;

    @PrePersist
    protected void generateUuid() {
        if (llmKeyNo == null) {
            llmKeyNo = UUID.randomUUID();
        }
    }

    public void updateStrategy(Strategy strategy) {
        this.strategy = strategy;
    }

    public void updateApiKey(String apiKey) {
        this.apiKey = apiKey;
    }
}
