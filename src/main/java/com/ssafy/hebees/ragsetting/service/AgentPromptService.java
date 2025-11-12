package com.ssafy.hebees.ragsetting.service;

import com.ssafy.hebees.common.dto.ListResponse;
import com.ssafy.hebees.ragsetting.dto.request.AgentPromptCreateRequest;
import com.ssafy.hebees.ragsetting.dto.request.AgentPromptUpdateRequest;
import com.ssafy.hebees.ragsetting.dto.response.AgentPromptResponse;
import java.util.UUID;

public interface AgentPromptService {

    AgentPromptResponse create(AgentPromptCreateRequest request);

    AgentPromptResponse get(UUID agentPromptNo);

    ListResponse<AgentPromptResponse> list();

    AgentPromptResponse update(UUID agentPromptNo, AgentPromptUpdateRequest request);

    void delete(UUID agentPromptNo);
}

