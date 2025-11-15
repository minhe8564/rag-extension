package com.ssafy.hebees.dashboard.model.repository;

import com.ssafy.hebees.dashboard.entity.ModelAggregateHourly;
import java.time.LocalDateTime;
import java.util.List;

public interface ModelAggregateHourlyRepositoryCustom {

    List<ModelAggregateHourly> findBetween(LocalDateTime startInclusive,
        LocalDateTime endExclusive);
}

