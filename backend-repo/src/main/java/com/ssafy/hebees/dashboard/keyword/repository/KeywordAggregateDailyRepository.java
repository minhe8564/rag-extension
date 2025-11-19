package com.ssafy.hebees.dashboard.keyword.repository;

import com.ssafy.hebees.dashboard.keyword.entity.KeywordAggregateDaily;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface KeywordAggregateDailyRepository
    extends JpaRepository<KeywordAggregateDaily, UUID>, KeywordAggregateDailyRepositoryCustom {

}
