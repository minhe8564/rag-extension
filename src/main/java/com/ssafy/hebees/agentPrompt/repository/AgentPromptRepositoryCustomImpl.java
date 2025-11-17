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

    private static final QAgentPrompt agentPrompt = QAgentPrompt.agentPrompt;
    private final JPAQueryFactory queryFactory;

    public boolean existsByNameIgnoreCase(String name, UUID excludeAgentPromptNo){
        return !queryFactory
            .selectFrom(agentPrompt)
            .where(
                agentPrompt.name.equalsIgnoreCase(name),
                excludeSelf(excludeAgentPromptNo)
            )
            .fetch().isEmpty();
    }

    public Optional<AgentPrompt> findByNameIgnoreCase(String name){
        AgentPrompt result = queryFactory
            .selectFrom(agentPrompt)
            .where(
                agentPrompt.name.equalsIgnoreCase(name)
            )
            .fetchFirst();
        return Optional.ofNullable(result);
    }

    private BooleanExpression excludeSelf(UUID agentPromptNo) {
        return agentPromptNo != null
            ? agentPrompt.agentPromptNo.ne(agentPromptNo)
            : null;
    }
}