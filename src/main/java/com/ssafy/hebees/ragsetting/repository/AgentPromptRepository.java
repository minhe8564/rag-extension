package com.ssafy.hebees.ragsetting.repository;

import com.ssafy.hebees.ragsetting.entity.AgentPrompt;
import java.util.List;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface AgentPromptRepository extends JpaRepository<AgentPrompt, UUID> {

    boolean existsByNameIgnoreCase(String name);

    boolean existsByNameIgnoreCaseAndAgentPromptNoNot(String name, UUID agentPromptNo);

    List<AgentPrompt> findByName(String name);
}

