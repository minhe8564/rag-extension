package com.ssafy.hebees.dashboard.repository;

import com.ssafy.hebees.dashboard.entity.ErrorAggregateHourly;
import java.time.LocalDateTime;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ErrorAggregateHourlyRepository
    extends JpaRepository<ErrorAggregateHourly, LocalDateTime>, ErrorAggregateHourlyRepositoryCustom {
}

