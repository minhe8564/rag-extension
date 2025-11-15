package com.ssafy.hebees.dashboard.model.repository;

import com.ssafy.hebees.dashboard.entity.ChatbotAggregateHourly;
import java.time.LocalDateTime;
import org.springframework.data.jpa.repository.JpaRepository;

public interface UsageAggregateHourlyRepository
    extends JpaRepository<ChatbotAggregateHourly, LocalDateTime>,
    UsageAggregateHourlyRepositoryCustom {

}

