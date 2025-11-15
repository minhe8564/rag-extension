package com.ssafy.hebees.ragsetting.entity;

import com.ssafy.hebees.common.entity.BaseEntity;
import jakarta.persistence.CascadeType;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.Id;
import jakarta.persistence.OneToMany;
import jakarta.persistence.PrePersist;
import jakarta.persistence.Table;
import jakarta.persistence.UniqueConstraint;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Entity
@Table(
    name = "STRATEGY_TYPE",
    uniqueConstraints = {
        @UniqueConstraint(name = "UK_STRATEGY_TYPE_NAME", columnNames = "NAME")
    }
)
@Getter
@Builder(toBuilder = true)
@AllArgsConstructor(access = AccessLevel.PRIVATE)
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class StrategyType extends BaseEntity {

    @Id
    @Column(name = "STRATEGY_TYPE_NO", columnDefinition = "BINARY(16)", nullable = false)
    private UUID strategyTypeNo;

    @Column(name = "NAME", length = 255, nullable = false)
    private String name;

    @Builder.Default
    @OneToMany(mappedBy = "strategyType", cascade = CascadeType.ALL, orphanRemoval = true, fetch = FetchType.LAZY)
    private List<Strategy> strategies = new ArrayList<>();

    @PrePersist
    private void prePersist() {
        if (strategyTypeNo == null) {
            strategyTypeNo = UUID.randomUUID();
        }
    }

    public void addStrategy(Strategy strategy) {
        strategies.add(strategy);
        strategy.setStrategyType(this);
    }

    public void removeStrategy(Strategy strategy) {
        strategies.remove(strategy);
        strategy.setStrategyType(null);
    }
}
