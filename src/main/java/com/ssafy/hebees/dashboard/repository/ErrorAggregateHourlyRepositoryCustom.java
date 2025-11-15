package com.ssafy.hebees.dashboard.repository;

import java.time.LocalDateTime;

public interface ErrorAggregateHourlyRepositoryCustom {

    Long sumTotalErrorCountBetween(LocalDateTime start, LocalDateTime end);

    Long sumTotalErrorCount();
}

