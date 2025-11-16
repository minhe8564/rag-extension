package com.ssafy.hebees.chat.service;

import com.ssafy.hebees.chat.client.dto.LlmChatMessage;
import com.ssafy.hebees.chat.client.dto.LlmChatResult;
import com.ssafy.hebees.chat.dto.request.SessionCreateRequest;
import com.ssafy.hebees.common.exception.BusinessException;
import com.ssafy.hebees.AgentPrompt.entity.AgentPrompt;
import com.ssafy.hebees.ragsetting.entity.Strategy;
import com.ssafy.hebees.AgentPrompt.repository.AgentPromptRepository;
import com.ssafy.hebees.ragsetting.repository.StrategyRepository;
import java.util.List;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

@Slf4j
@Service
@RequiredArgsConstructor
public class SessionTitleServiceImpl implements SessionTitleService {

    private static final String TITLE_PROMPT_NAME = "Title Generation";
    private static final String TITLE_PROMPT_FALLBACK = """
        You are an assistant that reads the user's question and replies only with a concise Korean session title under 15 characters. Do not include punctuation or any extra text.
        """;
    private static final String TITLE_STRATEGY_NAME = "GPT-4o";
    private static final String TITLE_STRATEGY_CODE_PREFIX = "GEN";

    private final LlmChatGateway llmChatGateway;
    private final AgentPromptRepository agentPromptRepository;
    private final StrategyRepository strategyRepository;

    @Override
    public String generate(String query) {
        String sanitizedQuery = query != null ? query.strip() : "";
        if (!StringUtils.hasText(sanitizedQuery)) {
            return SessionCreateRequest.DEFAULT_TITLE;
        }

        Strategy strategy = strategyRepository
            .findByNameAndCodeStartingWith(TITLE_STRATEGY_NAME, TITLE_STRATEGY_CODE_PREFIX)
            .orElse(null);
        if (strategy == null) {
            log.warn("세션 제목 생성을 위한 LLM 전략을 찾을 수 없습니다. name={}, codePrefix={}",
                TITLE_STRATEGY_NAME, TITLE_STRATEGY_CODE_PREFIX);
            return fallbackTitle(sanitizedQuery);
        }

        String prompt = agentPromptRepository.findByName(TITLE_PROMPT_NAME)
            .map(AgentPrompt::getContent)
            .filter(StringUtils::hasText)
            .orElse(TITLE_PROMPT_FALLBACK)
            .strip();

        try {
            LlmChatResult result = llmChatGateway.chatWithSystem(
                strategy.getStrategyNo(),
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

