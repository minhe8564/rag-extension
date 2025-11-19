package com.ssafy.hebees.dashboard.repository;

import com.querydsl.jpa.impl.JPAQueryFactory;
import com.ssafy.hebees.dashboard.entity.QErrorAggregateHourly;
import java.time.LocalDateTime;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

@Repository
@RequiredArgsConstructor
public class ErrorAggregateHourlyRepositoryImpl
    implements ErrorAggregateHourlyRepositoryCustom {

    private final JPAQueryFactory queryFactory;
    private final QErrorAggregateHourly errorAggregateHourly =
        QErrorAggregateHourly.errorAggregateHourly;

    @Override
    public Long sumTotalErrorCountBetween(LocalDateTime start, LocalDateTime end) {
        Long sum = queryFactory
            .select(errorAggregateHourly.totalErrorCount.sum())
            .from(errorAggregateHourly)
            .where(
                errorAggregateHourly.errorAggregateDatetime.goe(start),
                errorAggregateHourly.errorAggregateDatetime.lt(end)
            )
            .fetchOne();

        return sum != null ? sum : 0L;
    }

    @Override
    public Long sumTotalErrorCount() {
        Long sum = queryFactory
            .select(errorAggregateHourly.totalErrorCount.sum())
            .from(errorAggregateHourly)
            .fetchOne();

        return sum != null ? sum : 0L;
    }
}

