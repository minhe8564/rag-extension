package com.ssafy.hebees.dashboard.model.repository;

import com.querydsl.jpa.impl.JPAQueryFactory;
import com.ssafy.hebees.dashboard.entity.QChatbotAggregateHourly;
import com.ssafy.hebees.dashboard.entity.ChatbotAggregateHourly;
import java.time.LocalDateTime;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

@Repository
@RequiredArgsConstructor
public class UsageAggregateHourlyRepositoryImpl implements UsageAggregateHourlyRepositoryCustom {

    private final JPAQueryFactory queryFactory;
    private final QChatbotAggregateHourly chatbotAggregateHourly = QChatbotAggregateHourly.chatbotAggregateHourly;

    @Override
    public List<ChatbotAggregateHourly> findBetween(LocalDateTime startInclusive,
        LocalDateTime endExclusive) {
        return queryFactory
            .selectFrom(chatbotAggregateHourly)
            .where(
                chatbotAggregateHourly.aggregateDateTime.goe(startInclusive),
                chatbotAggregateHourly.aggregateDateTime.lt(endExclusive)
            )
            .orderBy(chatbotAggregateHourly.aggregateDateTime.asc())
            .fetch();
    }
}

