package com.ssafy.hebees.agentPrompt.repository;

import com.ssafy.hebees.agentPrompt.entity.AgentPrompt;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface AgentPromptRepository extends JpaRepository<AgentPrompt, UUID>, AgentPromptRepositoryCustom {
}
