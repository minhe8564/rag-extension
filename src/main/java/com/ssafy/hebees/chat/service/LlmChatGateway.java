package com.ssafy.hebees.chat.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.ssafy.hebees.chat.client.LlmChatClient;
import com.ssafy.hebees.chat.client.LlmProvider;
import com.ssafy.hebees.chat.client.dto.LlmChatMessage;
import com.ssafy.hebees.chat.client.dto.LlmChatRequest;
import com.ssafy.hebees.chat.client.dto.LlmChatResult;
import com.ssafy.hebees.chat.config.AnthropicProperties;
import com.ssafy.hebees.chat.config.GeminiProperties;
import com.ssafy.hebees.chat.config.OpenAiProperties;
import com.ssafy.hebees.chat.config.RunpodProperties;
import com.ssafy.hebees.common.exception.BusinessException;
import com.ssafy.hebees.common.exception.ErrorCode;
import com.ssafy.hebees.ragsetting.entity.LlmKey;
import com.ssafy.hebees.ragsetting.entity.Strategy;
import com.ssafy.hebees.ragsetting.repository.LlmKeyRepository;
import com.ssafy.hebees.ragsetting.repository.StrategyRepository;
import java.time.Duration;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.util.CollectionUtils;
import org.springframework.util.StringUtils;

@Slf4j
@Service
@RequiredArgsConstructor
public class LlmChatGateway {

    private final StrategyRepository strategyRepository;
    private final LlmKeyRepository llmKeyRepository;
    private final List<LlmChatClient> clients;
    private final OpenAiProperties openAiProperties;
    private final GeminiProperties geminiProperties;
    private final AnthropicProperties anthropicProperties;
    private final RunpodProperties runpodProperties;

    public LlmChatResult chat(UUID userNo, UUID strategyNo, List<LlmChatMessage> messages) {
        if (strategyNo == null) {
            throw new BusinessException(ErrorCode.INVALID_INPUT);
        }
        if (CollectionUtils.isEmpty(messages)) {
            throw new BusinessException(ErrorCode.INVALID_INPUT);
        }

        Strategy strategy = strategyRepository.findByStrategyNo(strategyNo)
            .orElseThrow(() -> new BusinessException(ErrorCode.NOT_FOUND));

        LlmProvider provider = resolveProvider(strategy);
        LlmChatClient client = clients.stream()
            .filter(candidate -> candidate.supports(provider))
            .findFirst()
            .orElseThrow(() -> new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR));

        String apiKey = resolveApiKey(userNo, provider, strategy);
        String model = resolveModel(provider, strategy);
        JsonNode parameter = strategy.getParameter();

        LlmChatRequest request = new LlmChatRequest(
            provider,
            model,
            apiKey,
            messages,
            parameter,
            strategy.getName(),
            strategy.getCode()
        );

        long startedAt = System.nanoTime();
        LlmChatResult result = client.chat(request);
        long responseTimeMs = Duration.ofNanos(System.nanoTime() - startedAt).toMillis();

        if (result == null || !StringUtils.hasText(result.content())) {
            log.error("LLM 응답이 비어있습니다. provider={}, strategy={}", provider, strategyNo);
            throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
        }

        String trimmedContent = result.content() != null ? result.content().strip() : null;
        return new LlmChatResult(
            result.role(),
            trimmedContent,
            result.inputTokens(),
            result.outputTokens(),
            result.totalTokens(),
            responseTimeMs
        );
    }

    private LlmProvider resolveProvider(Strategy strategy) {
        JsonNode parameter = strategy.getParameter();
        if (parameter != null) {
            String provider = extractText(parameter, "provider")
                .orElseGet(() -> extractText(parameter, "vendor").orElse(null));
            if (StringUtils.hasText(provider)) {
                return LlmProvider.fromIdentifier(provider)
                    .orElseThrow(() -> new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR));
            }
        }

        for (String identifier : List.of(strategy.getCode(), strategy.getName())) {
            if (!StringUtils.hasText(identifier)) {
                continue;
            }
            Optional<LlmProvider> provider = LlmProvider.fromIdentifier(identifier);
            if (provider.isPresent()) {
                return provider.get();
            }
        }

        log.error("LLM 공급자를 판별할 수 없습니다. strategyNo={}", strategy.getStrategyNo());
        throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
    }

    private String resolveModel(LlmProvider provider, Strategy strategy) {
        JsonNode parameter = strategy.getParameter();
        String model = extractText(parameter, "model").orElse(null);
        if (StringUtils.hasText(model)) {
            return model;
        }

        return switch (provider) {
            case CHATGPT -> openAiProperties.getDefaultModel();
            case GEMINI -> geminiProperties.getDefaultModel();
            case CLAUDE -> anthropicProperties.getDefaultModel();
            case RUNPOD -> runpodProperties.getModel();
        };
    }

    private String resolveApiKey(UUID userNo, LlmProvider provider, Strategy strategy) {
        if (userNo == null) {
            throw new BusinessException(ErrorCode.INVALID_INPUT);
        }

        Optional<String> userKey = llmKeyRepository
            .findByUser_UuidAndStrategy_StrategyNo(userNo, strategy.getStrategyNo())
            .map(LlmKey::getApiKey)
            .filter(StringUtils::hasText);

        if (userKey.isPresent()) {
            return userKey.get();
        }

        String fallback = fallbackApiKey(provider, strategy);
        if (StringUtils.hasText(fallback)) {
            return fallback;
        }

        log.warn("LLM API 키를 찾을 수 없습니다. provider={}, userNo={}, strategy={}",
            provider, userNo, strategy.getStrategyNo());
        throw new BusinessException(ErrorCode.NOT_FOUND);
    }

    private String fallbackApiKey(LlmProvider provider, Strategy strategy) {
        JsonNode parameter = strategy.getParameter();
        String parameterKey = extractText(parameter, "apiKey").orElse(null);
        if (StringUtils.hasText(parameterKey)) {
            return parameterKey;
        }

        return switch (provider) {
            case CHATGPT -> openAiProperties.getDefaultApiKey();
            case GEMINI -> geminiProperties.getDefaultApiKey();
            case CLAUDE -> anthropicProperties.getDefaultApiKey();
            case RUNPOD -> runpodProperties.getApiKey();
        };
    }

    private Optional<String> extractText(JsonNode node, String fieldName) {
        if (node == null || !StringUtils.hasText(fieldName)) {
            return Optional.empty();
        }
        JsonNode value = node.path(fieldName);
        if (value.isTextual()) {
            String text = value.asText();
            if (StringUtils.hasText(text)) {
                return Optional.of(text);
            }
        }
        return Optional.empty();
    }
}

