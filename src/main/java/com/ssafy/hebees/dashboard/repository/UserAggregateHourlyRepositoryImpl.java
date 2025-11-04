package com.ssafy.hebees.dashboard.repository;

import com.querydsl.jpa.impl.JPAQueryFactory;
import com.ssafy.hebees.dashboard.entity.QUserAggregateHourly;
import java.time.LocalDateTime;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

@Repository
@RequiredArgsConstructor
public class UserAggregateHourlyRepositoryImpl implements UserAggregateHourlyRepositoryCustom {

    private final JPAQueryFactory queryFactory;
    private final QUserAggregateHourly userAggregateHourly = QUserAggregateHourly.userAggregateHourly;

    @Override
    public Long sumAccessUserCountBetween(LocalDateTime start, LocalDateTime end) {
        Long sum = queryFactory
            .select(userAggregateHourly.accessUserCount.sum())
            .from(userAggregateHourly)
            .where(
                userAggregateHourly.aggregateDatetime.goe(start),
                userAggregateHourly.aggregateDatetime.lt(end)
            )
            .fetchOne();

        return sum != null ? sum : 0L;
    }
}

