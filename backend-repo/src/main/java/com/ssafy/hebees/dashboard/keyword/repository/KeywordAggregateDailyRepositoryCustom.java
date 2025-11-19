package com.ssafy.hebees.dashboard.keyword.repository;

import com.ssafy.hebees.dashboard.keyword.dto.response.TrendKeywordListResponse.TrendKeyword;
import com.ssafy.hebees.dashboard.keyword.entity.KeywordAggregateDaily;
import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

public interface KeywordAggregateDailyRepositoryCustom {

    Optional<KeywordAggregateDaily> findByAggregateDateAndKeyword(
        LocalDate aggregateDate, String keyword);

    List<TrendKeyword> sumTopKeywords(LocalDate startInclusive, LocalDate endInclusive, int limit);
}
