package com.ssafy.hebees.dashboard.repository;

import com.querydsl.jpa.impl.JPAQueryFactory;
import com.ssafy.hebees.dashboard.dto.response.TrendKeyword;
import com.ssafy.hebees.dashboard.entity.QKeywordAggregateDaily;
import java.time.LocalDate;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

@Repository
@RequiredArgsConstructor
public class KeywordAggregateDailyRepositoryImpl implements KeywordAggregateDailyRepositoryCustom {

    private final JPAQueryFactory queryFactory;
    private final QKeywordAggregateDaily keywordAggregateDaily = QKeywordAggregateDaily.keywordAggregateDaily;

    @Override
    public List<TrendKeyword> sumTopKeywords(LocalDate startInclusive, LocalDate endInclusive,
        int limit) {
        return queryFactory
            .select(keywordAggregateDaily.keyword,
                keywordAggregateDaily.frequency.sum().coalesce(0))
            .from(keywordAggregateDaily)
            .where(
                keywordAggregateDaily.aggregateDate.goe(startInclusive),
                keywordAggregateDaily.aggregateDate.loe(endInclusive)
            )
            .groupBy(keywordAggregateDaily.keyword)
            .orderBy(keywordAggregateDaily.frequency.sum().desc(),
                keywordAggregateDaily.keyword.asc())
            .limit(limit)
            .fetch()
            .stream()
            .map(tuple -> new TrendKeyword(tuple.get(keywordAggregateDaily.keyword),
                tuple.get(keywordAggregateDaily.frequency.sum().coalesce(0)), 0f))
            .toList();
    }
}

