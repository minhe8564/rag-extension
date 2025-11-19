package com.ssafy.hebees.chat.client;

import com.fasterxml.jackson.databind.JsonNode;
import com.ssafy.hebees.chat.client.dto.LlmChatMessage;
import com.ssafy.hebees.chat.client.dto.LlmChatRequest;
import com.ssafy.hebees.chat.client.dto.LlmChatResult;
import com.ssafy.hebees.chat.client.dto.RunpodChatMessage;
import com.ssafy.hebees.chat.client.dto.RunpodChatResult;
import com.ssafy.hebees.chat.config.RunpodProperties;
import com.ssafy.hebees.common.exception.BusinessException;
import com.ssafy.hebees.common.exception.ErrorCode;
import java.util.List;
import java.util.Objects;
import java.util.stream.Collectors;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.util.CollectionUtils;
import org.springframework.util.StringUtils;

@Slf4j
@Component
@RequiredArgsConstructor
public class RunpodLlmChatClient implements LlmChatClient {

    private final RunpodClient runpodClient;
    private final RunpodProperties properties;

    @Override
    public boolean supports(LlmProvider provider) {
        return provider == LlmProvider.RUNPOD;
    }

    @Override
    public LlmChatResult chat(LlmChatRequest request) {
        List<LlmChatMessage> chatMessages = request.messages();
        if (CollectionUtils.isEmpty(chatMessages)) {
            log.error("Runpod 요청 메시지가 비어있습니다. strategy={}", request.strategyCode());
            throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
        }

        List<RunpodChatMessage> messages = chatMessages.stream()
            .filter(Objects::nonNull)
            .filter(message -> StringUtils.hasText(message.content()))
            .map(message -> RunpodChatMessage.of(normalizeRole(message.role()), message.content()))
            .collect(Collectors.toList());

        if (messages.isEmpty()) {
            log.error("Runpod 메시지 변환 결과가 비어있습니다. strategy={}", request.strategyCode());
            throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
        }

        String baseUrl = resolveBaseUrl(request.parameter());
        String model = resolveModel(request);

        String apiKey = request.apiKey();
        if (!StringUtils.hasText(apiKey)) {
            apiKey = properties.getApiKey();
        }

        RunpodChatResult result =
            runpodClient.chat(messages, baseUrl, model, apiKey);
        if (result == null || !StringUtils.hasText(result.content())) {
            log.error("Runpod 응답이 비어있습니다. strategy={}", request.strategyCode());
            throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
        }

        return new LlmChatResult(result.role(), result.content(), null, null, null, null);
    }

    private String resolveModel(LlmChatRequest request) {
        if (StringUtils.hasText(request.model())) {
            return request.model();
        }
        String override = extractText(request.parameter(), "model");
        if (StringUtils.hasText(override)) {
            return override;
        }
        if (StringUtils.hasText(properties.getModel())) {
            return properties.getModel();
        }
        log.error("Runpod 모델이 설정되지 않았습니다. strategy={}", request.strategyCode());
        throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
    }

    private String resolveBaseUrl(JsonNode parameter) {
        String override = extractText(parameter, "baseUrl");
        if (StringUtils.hasText(override)) {
            return override;
        }
        if (StringUtils.hasText(properties.getBaseUrl())) {
            return properties.getBaseUrl();
        }
        log.error("Runpod base URL을 확인할 수 없습니다.");
        throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
    }

    private String normalizeRole(String role) {
        if (!StringUtils.hasText(role)) {
            return "user";
        }
        return switch (role.strip().toLowerCase()) {
            case "assistant", "ai" -> "assistant";
            case "system" -> "system";
            case "tool" -> "tool";
            default -> "user";
        };
    }

    private String extractText(JsonNode parameter, String fieldName) {
        if (parameter == null || !StringUtils.hasText(fieldName)) {
            return null;
        }
        JsonNode node = parameter.path(fieldName);
        return node.isTextual() ? node.asText() : null;
    }
}

