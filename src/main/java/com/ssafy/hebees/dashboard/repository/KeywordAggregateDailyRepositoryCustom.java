package com.ssafy.hebees.dashboard.repository;

import com.ssafy.hebees.dashboard.dto.response.TrendKeyword;
import java.time.LocalDate;
import java.util.List;

public interface KeywordAggregateDailyRepositoryCustom {

    List<TrendKeyword> sumTopKeywords(LocalDate startInclusive, LocalDate endInclusive, int limit);
}

