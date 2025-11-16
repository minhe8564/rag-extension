package com.ssafy.hebees.AgentPrompt.repository;

import com.ssafy.hebees.AgentPrompt.entity.AgentPrompt;
import java.util.Optional;
import java.util.UUID;

public interface AgentPromptRepositoryCustom {

    boolean existsByNameIgnoreCase(String name, UUID agentPromptNo);

    Optional<AgentPrompt> findByName(String name);
}
