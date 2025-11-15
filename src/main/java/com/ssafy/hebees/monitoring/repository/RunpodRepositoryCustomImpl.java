package com.ssafy.hebees.monitoring.repository;

import com.querydsl.jpa.impl.JPAQueryFactory;
import com.ssafy.hebees.monitoring.entity.QRunpod;
import com.ssafy.hebees.monitoring.entity.Runpod;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

@Repository
@RequiredArgsConstructor
public class RunpodRepositoryCustomImpl implements RunpodRepositoryCustom {

    private final JPAQueryFactory queryFactory;
    private static final QRunpod runpod = QRunpod.runpod;

    @Override
    public Optional<Runpod> findByName(String name) {
        Runpod result = queryFactory
            .selectFrom(runpod)
            .where(runpod.name.eq(name))
            .fetchOne();

        return Optional.ofNullable(result);
    }
}
