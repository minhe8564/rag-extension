package com.ssafy.hebees.dashboard.keyword.repository;

import com.querydsl.jpa.impl.JPAQueryFactory;
import com.ssafy.hebees.dashboard.keyword.dto.response.TrendKeywordListResponse.TrendKeyword;
import com.ssafy.hebees.dashboard.keyword.entity.QKeywordAggregateDaily;
import com.ssafy.hebees.dashboard.keyword.entity.KeywordAggregateDaily;
import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

@Repository
@RequiredArgsConstructor
public class KeywordAggregateDailyRepositoryImpl implements KeywordAggregateDailyRepositoryCustom {

    private final JPAQueryFactory queryFactory;
    private static final QKeywordAggregateDaily keywordAggregateDaily = QKeywordAggregateDaily.keywordAggregateDaily;

    @Override
    public Optional<KeywordAggregateDaily> findByAggregateDateAndKeyword(
        LocalDate aggregateDate, String keyword) {
        KeywordAggregateDaily result = queryFactory
            .selectFrom(keywordAggregateDaily)
            .where(
                keywordAggregateDaily.aggregateDate.eq(aggregateDate),
                keywordAggregateDaily.keyword.eq(keyword)
            ).fetchFirst();

        return Optional.ofNullable(result);
    }

    @Override
    public List<TrendKeyword> sumTopKeywords(
        LocalDate startInclusive, LocalDate endInclusive, int limit) {
        return queryFactory
            .select(keywordAggregateDaily.keyword,
                keywordAggregateDaily.frequency.sum().coalesce(0L))
            .from(keywordAggregateDaily)
            .where(
                keywordAggregateDaily.aggregateDate.goe(startInclusive),
                keywordAggregateDaily.aggregateDate.loe(endInclusive)
            )
            .groupBy(keywordAggregateDaily.keyword)
            .orderBy(
                keywordAggregateDaily.frequency.sum().desc(),
                keywordAggregateDaily.keyword.asc()
            )
            .limit(limit)
            .fetch()
            .stream()
            .map(tuple -> new TrendKeyword(tuple.get(
                    keywordAggregateDaily.keyword),
                    tuple.get(keywordAggregateDaily.frequency.sum().coalesce(0L)),
                    0f
                )
            )
            .toList();
    }
}
