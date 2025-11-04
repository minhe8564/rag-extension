package com.ssafy.hebees.dashboard.repository;

import com.ssafy.hebees.dashboard.entity.UsageAggregateHourly;
import java.time.LocalDateTime;
import java.util.List;

public interface UsageAggregateHourlyRepositoryCustom {

    List<UsageAggregateHourly> findBetween(LocalDateTime startInclusive,
        LocalDateTime endExclusive);
}

