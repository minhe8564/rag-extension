package com.ssafy.hebees.dashboard.model.repository;

import com.querydsl.jpa.impl.JPAQueryFactory;
import com.ssafy.hebees.dashboard.entity.ModelAggregateHourly;
import com.ssafy.hebees.dashboard.entity.QModelAggregateHourly;
import java.time.LocalDateTime;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

@Repository
@RequiredArgsConstructor
public class ModelAggregateHourlyRepositoryImpl implements ModelAggregateHourlyRepositoryCustom {

    private final JPAQueryFactory queryFactory;
    private final QModelAggregateHourly modelAggregateHourly = QModelAggregateHourly.modelAggregateHourly;

    @Override
    public List<ModelAggregateHourly> findBetween(LocalDateTime startInclusive,
        LocalDateTime endExclusive) {
        return queryFactory
            .selectFrom(modelAggregateHourly)
            .where(
                modelAggregateHourly.aggregateDateTime.goe(startInclusive),
                modelAggregateHourly.aggregateDateTime.lt(endExclusive)
            )
            .orderBy(
                modelAggregateHourly.llmNo.asc(),
                modelAggregateHourly.aggregateDateTime.asc()
            )
            .fetch();
    }
}

