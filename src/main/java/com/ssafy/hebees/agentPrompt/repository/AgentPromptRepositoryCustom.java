package com.ssafy.hebees.agentPrompt.repository;

import com.ssafy.hebees.agentPrompt.entity.AgentPrompt;
import java.util.Optional;
import java.util.UUID;

public interface AgentPromptRepositoryCustom {

    boolean existsByNameIgnoreCase(String name, UUID agentPromptNo);

    Optional<AgentPrompt> findByName(String name);
}
