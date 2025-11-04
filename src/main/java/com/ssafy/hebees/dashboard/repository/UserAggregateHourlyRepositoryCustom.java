package com.ssafy.hebees.dashboard.repository;

import java.time.LocalDateTime;

public interface UserAggregateHourlyRepositoryCustom {

    Long sumAccessUserCountBetween(LocalDateTime start, LocalDateTime end);

    Long sumAccessUserCount();
}

