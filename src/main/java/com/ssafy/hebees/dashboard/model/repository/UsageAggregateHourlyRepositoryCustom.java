package com.ssafy.hebees.dashboard.model.repository;

import com.ssafy.hebees.dashboard.entity.ChatbotAggregateHourly;
import java.time.LocalDateTime;
import java.util.List;

public interface UsageAggregateHourlyRepositoryCustom {

    List<ChatbotAggregateHourly> findBetween(LocalDateTime startInclusive,
        LocalDateTime endExclusive);
}

