package com.ssafy.hebees.dashboard.repository;

import com.ssafy.hebees.dashboard.entity.ChatbotAggregateHourly;
import java.time.LocalDateTime;
import org.springframework.data.jpa.repository.JpaRepository;

public interface UsageAggregateHourlyRepository
    extends JpaRepository<ChatbotAggregateHourly, LocalDateTime>,
    UsageAggregateHourlyRepositoryCustom {

}

