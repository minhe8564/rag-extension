package com.ssafy.hebees.AgentPrompt.service;

import com.ssafy.hebees.common.dto.ListResponse;
import com.ssafy.hebees.common.exception.BusinessException;
import com.ssafy.hebees.common.exception.ErrorCode;
import com.ssafy.hebees.AgentPrompt.dto.requeset.AgentPromptUpsertRequest;
import com.ssafy.hebees.AgentPrompt.dto.response.AgentPromptResponse;
import com.ssafy.hebees.AgentPrompt.entity.AgentPrompt;
import com.ssafy.hebees.AgentPrompt.repository.AgentPromptRepository;
import com.ssafy.hebees.common.util.ValidationUtil;
import java.util.List;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Slf4j
@Service
@RequiredArgsConstructor
@Transactional
public class AgentPromptServiceImpl implements AgentPromptService {

    private final AgentPromptRepository agentPromptRepository;


    @Override
    @Transactional(readOnly = true)
    public ListResponse<AgentPromptResponse> listAgentPrompts() {
        List<AgentPrompt> list = agentPromptRepository.findAll();
        return ListResponse.of(list.stream().map(AgentPromptServiceImpl::toResponse).toList());
    }

    @Override
    @Transactional(readOnly = true)
    public AgentPromptResponse getAgentPrompt(UUID agentPromptNo) {
        ValidationUtil.require(agentPromptNo);

        AgentPrompt agentPrompt = fetchAgentPrompt(agentPromptNo);
        return toResponse(agentPrompt);
    }

    @Override
    public AgentPromptResponse createAgentPrompt(AgentPromptUpsertRequest request) {
        String name = ValidationUtil.require(request.name());
        String description = ValidationUtil.orElse(request.description(), null);
        String content = ValidationUtil.require(request.content());

        ensureUniqueAgentPrompt(name, null);

        AgentPrompt saved = agentPromptRepository.save(
            AgentPrompt.builder()
                .name(name)
                .description(description)
                .content(content)
                .build()
        );

        return toResponse(saved);
    }

    @Override
    public AgentPromptResponse updateAgentPrompt(UUID agentPromptNo, AgentPromptUpsertRequest request) {
        ValidationUtil.require(agentPromptNo);
        AgentPrompt agentPrompt = fetchAgentPrompt(agentPromptNo);

        String name = ValidationUtil.orElse(request.name(), agentPrompt.getName());
        String description = ValidationUtil.orElse(request.description(),
            agentPrompt.getDescription());
        String content = ValidationUtil.orElse(request.content(), agentPrompt.getContent());

        ensureUniqueAgentPrompt(name, agentPromptNo);

        agentPrompt.update(name, description, content);

        AgentPrompt saved = agentPromptRepository.save(agentPrompt);

        return toResponse(saved);
    }

    @Override
    public void deleteAgentPrompt(UUID agentPromptNo) {
        AgentPrompt agentPrompt = fetchAgentPrompt(agentPromptNo);

        agentPromptRepository.delete(agentPrompt);
    }

    private void ensureUniqueAgentPrompt(String name, UUID agentPromptNo) {
        if (agentPromptRepository.existsByNameIgnoreCase(name, agentPromptNo)) {
            log.warn("AgentPrompt 중복 이름 존재: name={}", name);
            throw new BusinessException(ErrorCode.ALREADY_EXISTS);
        }
    }

    private AgentPrompt fetchAgentPrompt(UUID agentPromptNo) {
        ValidationUtil.require(agentPromptNo);
        return agentPromptRepository.findById(agentPromptNo)
            .orElseThrow(() -> {
                log.warn("AgentPrompt 조회 실패 - 존재하지 않음: agentPromptNo={}", agentPromptNo);
                return new BusinessException(ErrorCode.NOT_FOUND);
            });
    }

    private static AgentPromptResponse toResponse(AgentPrompt agentPrompt) {
        return new AgentPromptResponse(
            agentPrompt.getAgentPromptNo(),
            agentPrompt.getName(),
            agentPrompt.getDescription(),
            agentPrompt.getContent()
        );
    }
}
