package com.ssafy.hebees.dashboard.repository;

import com.querydsl.jpa.impl.JPAQueryFactory;
import com.ssafy.hebees.dashboard.entity.QUsageAggregateHourly;
import com.ssafy.hebees.dashboard.entity.UsageAggregateHourly;
import java.time.LocalDateTime;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

@Repository
@RequiredArgsConstructor
public class UsageAggregateHourlyRepositoryImpl implements UsageAggregateHourlyRepositoryCustom {

    private final JPAQueryFactory queryFactory;
    private final QUsageAggregateHourly usageAggregateHourly = QUsageAggregateHourly.usageAggregateHourly;

    @Override
    public List<UsageAggregateHourly> findBetween(LocalDateTime startInclusive,
        LocalDateTime endExclusive) {
        return queryFactory
            .selectFrom(usageAggregateHourly)
            .where(
                usageAggregateHourly.aggregateDateTime.goe(startInclusive),
                usageAggregateHourly.aggregateDateTime.lt(endExclusive)
            )
            .orderBy(usageAggregateHourly.aggregateDateTime.asc())
            .fetch();
    }
}

