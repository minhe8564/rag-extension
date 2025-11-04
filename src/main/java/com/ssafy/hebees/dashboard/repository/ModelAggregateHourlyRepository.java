package com.ssafy.hebees.dashboard.repository;

import com.ssafy.hebees.dashboard.entity.ModelAggregateHourly;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ModelAggregateHourlyRepository
    extends JpaRepository<ModelAggregateHourly, UUID>, ModelAggregateHourlyRepositoryCustom {
}

