package com.ssafy.hebees.AgentPrompt.repository;

import com.ssafy.hebees.AgentPrompt.entity.AgentPrompt;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface AgentPromptRepository extends JpaRepository<AgentPrompt, UUID>, AgentPromptRepositoryCustom {
}
