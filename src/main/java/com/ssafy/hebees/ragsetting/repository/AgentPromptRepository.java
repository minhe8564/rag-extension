package com.ssafy.hebees.ragsetting.repository;

import com.ssafy.hebees.ragsetting.entity.AgentPrompt;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface AgentPromptRepository extends JpaRepository<AgentPrompt, UUID> {

    boolean existsByNameIgnoreCase(String name);

    boolean existsByNameIgnoreCaseAndAgentPromptNoNot(String name, UUID agentPromptNo);

    Optional<AgentPrompt> findByName(String name);
}

