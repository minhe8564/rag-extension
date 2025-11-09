package com.ssafy.hebees.dashboard.repository;

import com.ssafy.hebees.dashboard.entity.KeywordAggregateDaily;
import java.time.LocalDate;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface KeywordAggregateDailyRepository
    extends JpaRepository<KeywordAggregateDaily, UUID>, KeywordAggregateDailyRepositoryCustom {

    Optional<KeywordAggregateDaily> findByAggregateDateAndKeyword(LocalDate aggregateDate, String keyword);
}

