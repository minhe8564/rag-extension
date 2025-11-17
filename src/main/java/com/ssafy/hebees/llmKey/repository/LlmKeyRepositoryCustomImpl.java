package com.ssafy.hebees.llmKey.repository;

import com.querydsl.jpa.impl.JPAQueryFactory;
import com.ssafy.hebees.llmKey.entity.LlmKey;
import com.ssafy.hebees.llmKey.entity.QLlmKey;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

@Repository
@RequiredArgsConstructor
public class LlmKeyRepositoryCustomImpl implements LlmKeyRepositoryCustom {

    private final JPAQueryFactory queryFactory;
    private final QLlmKey llmKey = QLlmKey.llmKey;


    @Override
    public List<LlmKey> findAllByUserUuid(UUID userNo) {
        return queryFactory.selectFrom(llmKey)
            .where(llmKey.user.uuid.eq(userNo))
            .fetch();
    }

    @Override
    public Optional<LlmKey> findByUserUuidAndStrategyNo(UUID userNo, UUID strategyNo) {
        LlmKey result = queryFactory.selectFrom(llmKey)
            .where(llmKey.user.uuid.eq(userNo), llmKey.strategy.strategyNo.eq(strategyNo))
            .fetchOne();
        return Optional.ofNullable(result);
    }

    @Override
    public Optional<LlmKey> findSystemLlmKeyByStrategyNo(UUID strategyNo) {
        LlmKey result = queryFactory.selectFrom(llmKey)
            .where(
                llmKey.strategy.strategyNo.eq(strategyNo),
                llmKey.user.isNull()
            )
            .fetchFirst();
        return Optional.ofNullable(result);
    }
}
