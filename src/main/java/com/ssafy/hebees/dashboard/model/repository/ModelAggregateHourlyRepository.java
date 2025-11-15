package com.ssafy.hebees.dashboard.model.repository;

import com.ssafy.hebees.dashboard.entity.ModelAggregateHourly;
import java.time.LocalDateTime;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ModelAggregateHourlyRepository
    extends JpaRepository<ModelAggregateHourly, UUID>, ModelAggregateHourlyRepositoryCustom {

    Optional<ModelAggregateHourly> findByLlmNoAndAggregateDateTime(UUID llmNo,
        LocalDateTime aggregateDateTime);
}

