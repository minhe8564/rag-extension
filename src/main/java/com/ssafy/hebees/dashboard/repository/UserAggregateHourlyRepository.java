package com.ssafy.hebees.dashboard.repository;

import com.ssafy.hebees.dashboard.entity.UserAggregateHourly;
import java.time.LocalDateTime;
import org.springframework.data.jpa.repository.JpaRepository;

public interface UserAggregateHourlyRepository
    extends JpaRepository<UserAggregateHourly, LocalDateTime>, UserAggregateHourlyRepositoryCustom {
}

