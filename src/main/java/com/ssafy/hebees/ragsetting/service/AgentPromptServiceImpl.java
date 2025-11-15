package com.ssafy.hebees.ragsetting.service;

import com.ssafy.hebees.common.dto.ListResponse;
import com.ssafy.hebees.common.exception.BusinessException;
import com.ssafy.hebees.common.exception.ErrorCode;
import com.ssafy.hebees.ragsetting.dto.request.AgentPromptCreateRequest;
import com.ssafy.hebees.ragsetting.dto.request.AgentPromptUpdateRequest;
import com.ssafy.hebees.ragsetting.dto.response.AgentPromptResponse;
import com.ssafy.hebees.ragsetting.entity.AgentPrompt;
import com.ssafy.hebees.ragsetting.repository.AgentPromptRepository;
import java.util.Objects;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

@Slf4j
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class AgentPromptServiceImpl implements AgentPromptService {

    private final AgentPromptRepository agentPromptRepository;

    @Override
    @Transactional
    public AgentPromptResponse create(AgentPromptCreateRequest request) {
        String name = normalizeName(request.name());
        String description = trimToNull(request.description());
        String content = normalizeContent(request.content());

        if (agentPromptRepository.existsByNameIgnoreCase(name)) {
            log.warn("AgentPrompt 생성 실패 - 중복 이름: name={}", name);
            throw new BusinessException(ErrorCode.ALREADY_EXISTS);
        }

        AgentPrompt saved = agentPromptRepository.save(
            AgentPrompt.builder()
                .name(name)
                .description(description)
                .content(content)
                .build()
        );

        return AgentPromptResponse.from(saved);
    }

    @Override
    public AgentPromptResponse get(UUID agentPromptNo) {
        AgentPrompt agentPrompt = fetchAgentPrompt(agentPromptNo);
        return AgentPromptResponse.from(agentPrompt);
    }

    @Override
    public ListResponse<AgentPromptResponse> list() {
        return ListResponse.of(
            agentPromptRepository.findAll(Sort.by(Sort.Direction.ASC, "name")).stream()
                .map(AgentPromptResponse::from)
                .toList()
        );
    }

    @Override
    @Transactional
    @SuppressWarnings("null")
    public AgentPromptResponse update(UUID agentPromptNo, AgentPromptUpdateRequest request) {
        AgentPrompt agentPrompt = fetchAgentPrompt(agentPromptNo);

        String name = normalizeName(request.name());
        String description = trimToNull(request.description());
        String content = normalizeContent(request.content());

        if (agentPromptRepository.existsByNameIgnoreCaseAndAgentPromptNoNot(name, agentPromptNo)) {
            log.warn("AgentPrompt 수정 실패 - 중복 이름: agentPromptNo={}, name={}", agentPromptNo, name);
            throw new BusinessException(ErrorCode.ALREADY_EXISTS);
        }

        agentPrompt.update(name, description, content);

        @SuppressWarnings("null")
        AgentPrompt saved = agentPromptRepository.save(agentPrompt);

        return AgentPromptResponse.from(saved);
    }

    @Override
    @Transactional
    public void delete(UUID agentPromptNo) {
        AgentPrompt agentPrompt = fetchAgentPrompt(agentPromptNo);
        agentPromptRepository.delete(Objects.requireNonNull(agentPrompt));
    }

    private AgentPrompt fetchAgentPrompt(UUID agentPromptNo) {
        if (agentPromptNo == null) {
            throw new BusinessException(ErrorCode.INVALID_INPUT);
        }
        return agentPromptRepository.findById(agentPromptNo)
            .orElseThrow(() -> {
                log.warn("AgentPrompt 조회 실패 - 존재하지 않음: agentPromptNo={}", agentPromptNo);
                return new BusinessException(ErrorCode.NOT_FOUND);
            });
    }

    private String normalizeName(String name) {
        String trimmed = name != null ? name.trim() : null;
        if (!StringUtils.hasText(trimmed)) {
            throw new BusinessException(ErrorCode.BAD_REQUEST);
        }
        return trimmed;
    }

    private String normalizeContent(String content) {
        String trimmed = content != null ? content.trim() : null;
        if (!StringUtils.hasText(trimmed)) {
            throw new BusinessException(ErrorCode.BAD_REQUEST);
        }
        return trimmed;
    }

    private String trimToNull(String value) {
        if (value == null) {
            return null;
        }
        String trimmed = value.trim();
        return trimmed.isEmpty() ? null : trimmed;
    }
}

