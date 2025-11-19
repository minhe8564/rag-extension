package com.ssafy.hebees.dashboard.repository;

import java.time.LocalDateTime;

public interface DocumentAggregateHourlyRepositoryCustom {

    Long sumUploadCountBetween(LocalDateTime start, LocalDateTime end);

    Long sumUploadCount();
}

