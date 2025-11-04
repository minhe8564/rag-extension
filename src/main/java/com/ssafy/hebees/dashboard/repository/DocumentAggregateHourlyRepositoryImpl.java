package com.ssafy.hebees.dashboard.repository;

import com.querydsl.jpa.impl.JPAQueryFactory;
import com.ssafy.hebees.dashboard.entity.QDocumentAggregateHourly;
import java.time.LocalDateTime;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

@Repository
@RequiredArgsConstructor
public class DocumentAggregateHourlyRepositoryImpl
    implements DocumentAggregateHourlyRepositoryCustom {

    private final JPAQueryFactory queryFactory;
    private final QDocumentAggregateHourly documentAggregateHourly =
        QDocumentAggregateHourly.documentAggregateHourly;

    @Override
    public Long sumUploadCountBetween(LocalDateTime start, LocalDateTime end) {
        Long sum = queryFactory
            .select(documentAggregateHourly.uploadCount.sum())
            .from(documentAggregateHourly)
            .where(
                documentAggregateHourly.aggregateDatetime.goe(start),
                documentAggregateHourly.aggregateDatetime.lt(end)
            )
            .fetchOne();

        return sum != null ? sum : 0L;
    }

    @Override
    public Long sumUploadCount() {
        Long sum = queryFactory
            .select(documentAggregateHourly.uploadCount.sum())
            .from(documentAggregateHourly)
            .fetchOne();

        return sum != null ? sum : 0L;
    }
}

