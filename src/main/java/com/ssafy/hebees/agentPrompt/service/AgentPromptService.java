package com.ssafy.hebees.agentPrompt.service;

import com.ssafy.hebees.common.dto.ListResponse;
import com.ssafy.hebees.agentPrompt.dto.requeset.AgentPromptUpsertRequest;
import com.ssafy.hebees.agentPrompt.dto.response.AgentPromptResponse;
import java.util.UUID;

public interface AgentPromptService {

    AgentPromptResponse createAgentPrompt(AgentPromptUpsertRequest request);

    AgentPromptResponse getAgentPrompt(UUID agentPromptNo);

    ListResponse<AgentPromptResponse> listAgentPrompts();

    AgentPromptResponse updateAgentPrompt(UUID agentPromptNo, AgentPromptUpsertRequest request);

    void deleteAgentPrompt(UUID agentPromptNo);
}
