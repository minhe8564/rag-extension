package com.ssafy.hebees.dashboard.repository;

import com.ssafy.hebees.dashboard.entity.DocumentAggregateHourly;
import java.time.LocalDateTime;
import org.springframework.data.jpa.repository.JpaRepository;

public interface DocumentAggregateHourlyRepository
    extends JpaRepository<DocumentAggregateHourly, LocalDateTime>,
    DocumentAggregateHourlyRepositoryCustom {
}

