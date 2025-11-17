package com.ssafy.hebees.agentPrompt.repository;

import com.querydsl.core.types.dsl.BooleanExpression;
import com.querydsl.jpa.impl.JPAQueryFactory;
import com.ssafy.hebees.agentPrompt.entity.AgentPrompt;
import com.ssafy.hebees.agentPrompt.entity.QAgentPrompt;
import java.util.Optional;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

@Repository
@RequiredArgsConstructor
public class AgentPromptRepositoryCustomImpl implements AgentPromptRepositoryCustom {

    private final JPAQueryFactory queryFactory;
    private final QAgentPrompt agentPrompt = QAgentPrompt.agentPrompt;

    public boolean existsByNameIgnoreCase(String name, UUID agentPromptNo){
        return !queryFactory.selectFrom(agentPrompt)
            .where(agentPrompt.name.equalsIgnoreCase(name), excludeSelf(agentPromptNo))
            .fetch().isEmpty();
    }

    public Optional<AgentPrompt> findByName(String name){
        AgentPrompt result = queryFactory.selectFrom(agentPrompt)
            .where(agentPrompt.name.equalsIgnoreCase(name))
            .fetchFirst();
        return Optional.ofNullable(result);
    }

    private BooleanExpression excludeSelf(UUID agentPromptNo) {
        return agentPromptNo != null
            ? agentPrompt.agentPromptNo.ne(agentPromptNo)
            : null;
    }
}