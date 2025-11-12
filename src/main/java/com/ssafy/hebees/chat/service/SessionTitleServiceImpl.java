package com.ssafy.hebees.chat.service;

import com.ssafy.hebees.chat.client.RunpodClient;
import com.ssafy.hebees.chat.client.dto.RunpodChatMessage;
import com.ssafy.hebees.chat.client.dto.RunpodChatResult;
import com.ssafy.hebees.chat.dto.request.SessionCreateRequest;
import com.ssafy.hebees.common.exception.BusinessException;
import com.ssafy.hebees.ragsetting.entity.AgentPrompt;
import com.ssafy.hebees.ragsetting.repository.AgentPromptRepository;
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

    private final RunpodClient runpodClient;
    private final AgentPromptRepository agentPromptRepository;

    @Override
    public String generate(String query) {
        String sanitizedQuery = query != null ? query.strip() : "";
        if (!StringUtils.hasText(sanitizedQuery)) {
            return SessionCreateRequest.DEFAULT_TITLE;
        }

        try {
            AgentPrompt agentPrompt = agentPromptRepository.findByName("Title Generation").orElse(null);
            String prompt = agentPrompt != null ? agentPrompt.getContent() :
                "You are an assistant that reads the user's question and replies only with a concise Korean session title under 15 characters. Do not include punctuation or any extra text.";

            RunpodChatResult result = runpodClient.chat(List.of(
                RunpodChatMessage.of("system", prompt),
                RunpodChatMessage.of("user", sanitizedQuery)
            ));

            String title = Optional.ofNullable(result)
                .map(RunpodChatResult::content)
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
            log.warn("Runpod 세션 제목 생성 실패: {}", e.getMessage());
            return fallbackTitle(sanitizedQuery);
        } catch (Exception e) {
            log.error("Runpod 세션 제목 생성 중 알 수 없는 오류", e);
            return fallbackTitle(sanitizedQuery);
        }
    }

    private String fallbackTitle(String query) {
        String candidate = query.length() > 20 ? query.substring(0, 20) : query;
        return StringUtils.hasText(candidate) ? candidate : SessionCreateRequest.DEFAULT_TITLE;
    }
}

