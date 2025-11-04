package com.ssafy.hebees.dashboard.repository;

import com.ssafy.hebees.dashboard.entity.UsageAggregateHourly;
import java.time.LocalDateTime;
import org.springframework.data.jpa.repository.JpaRepository;

public interface UsageAggregateHourlyRepository
    extends JpaRepository<UsageAggregateHourly, LocalDateTime>, UsageAggregateHourlyRepositoryCustom {
}

