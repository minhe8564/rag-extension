package com.ssafy.hebees.dashboard.repository;

import com.ssafy.hebees.dashboard.entity.KeywordAggregateDaily;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface KeywordAggregateDailyRepository
    extends JpaRepository<KeywordAggregateDaily, UUID>, KeywordAggregateDailyRepositoryCustom {

}

