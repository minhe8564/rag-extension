package com.ssafy.hebees.chat.service;

import com.ssafy.hebees.chat.client.dto.LlmChatMessage;
import com.ssafy.hebees.chat.client.dto.LlmChatResult;
import com.ssafy.hebees.chat.dto.request.SessionCreateRequest;
import com.ssafy.hebees.common.exception.BusinessException;
import com.ssafy.hebees.agentPrompt.entity.AgentPrompt;
import com.ssafy.hebees.common.exception.ErrorCode;
import com.ssafy.hebees.agentPrompt.repository.AgentPromptRepository;
import com.ssafy.hebees.ragsetting.repository.StrategyRepository;
import jakarta.annotation.PostConstruct;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

@Slf4j
@Service
@RequiredArgsConstructor
public class SessionTitleServiceImpl implements SessionTitleService {

    private static final String PROMPT_NAME = "Title Generation";
    private static final String PROMPT_FALLBACK = """
        You are an assistant that reads the user's question and replies only with a concise Korean session title under 15 characters. Do not include punctuation or any extra text.
        """;

    private final LlmChatGateway llmChatGateway;
    private final AgentPromptRepository agentPromptRepository;
    private final StrategyRepository strategyRepository;

    private AgentPrompt agentPrompt;

    @PostConstruct
    private void init() {
        agentPrompt = agentPromptRepository.findByNameIgnoreCase(PROMPT_NAME)
            .orElseGet(() -> {
                AgentPrompt created = AgentPrompt.builder()
                    .name(PROMPT_NAME)
                    .content(PROMPT_FALLBACK)
                    .llm(strategyRepository.findByNameAndCodeStartingWith("GPT-4o", "GEN").orElseThrow(()->{
                        log.error("LLM GPT-4o strategy not found");
                        return new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
                    }))
                    .build();
                return agentPromptRepository.save(Objects.requireNonNull(created));
            });
    }

    @Override
    public String generate(String query) {
        if (!StringUtils.hasText(query)) {
            return SessionCreateRequest.DEFAULT_TITLE;
        }
        String sanitizedQuery = query.trim();

        if(agentPrompt == null){
            log.warn("세션 제목 생성을 위한 에이전트 프롬프트를 찾을 수 없습니다. name={}", PROMPT_NAME);
            return fallbackTitle(sanitizedQuery);
        }

        UUID llmNo = agentPrompt.getLlm().getStrategyNo();
        String prompt = agentPrompt.getContent();

        try {
            LlmChatResult result = llmChatGateway.chatWithSystem(
                llmNo,
                List.of(
                    new LlmChatMessage("system", prompt),
                    new LlmChatMessage("user", sanitizedQuery)
                )
            );

            String title = Optional.ofNullable(result)
                .map(LlmChatResult::content)
                .map(String::trim)
                .orElse("");

            if (!StringUtils.hasText(title)) {
                return fallbackTitle(sanitizedQuery);
            }

            if (title.length() > 20) {
                title = title.substring(0, 20);
            }

            return title;
        } catch (BusinessException e) {
            log.warn("LLM 세션 제목 생성 실패: {}", e.getMessage());
            return fallbackTitle(sanitizedQuery);
        } catch (Exception e) {
            log.error("LLM 세션 제목 생성 중 알 수 없는 오류", e);
            return fallbackTitle(sanitizedQuery);
        }
    }

    private String fallbackTitle(String query) {
        String candidate = query.length() > 20 ? query.substring(0, 20) : query;
        return StringUtils.hasText(candidate) ? candidate : SessionCreateRequest.DEFAULT_TITLE;
    }
}

