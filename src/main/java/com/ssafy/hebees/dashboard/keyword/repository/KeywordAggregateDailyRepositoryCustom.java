package com.ssafy.hebees.dashboard.keyword.repository;

import com.ssafy.hebees.dashboard.keyword.dto.response.TrendKeywordListResponse.TrendKeyword;
import java.time.LocalDate;
import java.util.List;

public interface KeywordAggregateDailyRepositoryCustom {

    List<TrendKeyword> sumTopKeywords(LocalDate startInclusive, LocalDate endInclusive, int limit);
}

