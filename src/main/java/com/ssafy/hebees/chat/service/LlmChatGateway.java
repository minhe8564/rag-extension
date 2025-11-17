package com.ssafy.hebees.chat.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.ssafy.hebees.chat.client.LlmChatClient;
import com.ssafy.hebees.chat.client.LlmProvider;
import com.ssafy.hebees.chat.client.StreamingLlmChatClient;
import com.ssafy.hebees.chat.client.dto.LlmChatMessage;
import com.ssafy.hebees.chat.client.dto.LlmChatRequest;
import com.ssafy.hebees.chat.client.dto.LlmChatResult;
import com.ssafy.hebees.chat.config.AnthropicProperties;
import com.ssafy.hebees.chat.config.GeminiProperties;
import com.ssafy.hebees.chat.config.OpenAiProperties;
import com.ssafy.hebees.chat.config.RunpodProperties;
import com.ssafy.hebees.common.exception.BusinessException;
import com.ssafy.hebees.common.exception.ErrorCode;
import com.ssafy.hebees.agentPrompt.entity.AgentPrompt;
import com.ssafy.hebees.llmKey.entity.LlmKey;
import com.ssafy.hebees.ragsetting.entity.Strategy;
import com.ssafy.hebees.agentPrompt.repository.AgentPromptRepository;
import com.ssafy.hebees.llmKey.repository.LlmKeyRepository;
import com.ssafy.hebees.ragsetting.repository.StrategyRepository;
import jakarta.annotation.PostConstruct;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.UUID;
import java.util.function.BiFunction;
import java.util.function.Consumer;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.util.CollectionUtils;
import org.springframework.util.StringUtils;

@Slf4j
@Service
@RequiredArgsConstructor
public class LlmChatGateway {

    private static final String PROMPT_NAME = "LLMPrompt";
    private static final String PROMPT_FALLBACK = """
        당신은 한국어 사용자를 위한 전문 챗봇입니다.
        - 가능한 한 자연스럽고 공손한 한국어로 답변합니다.
        - 사용자의 질문 의도를 정확히 이해하려 노력하며, 필요한 경우 명확화를 요청합니다.
        - 사실과 근거에 기반해 답변하고, 모르는 정보는 추측하지 말고 솔직하게 알 수 없다고 말합니다.
        - 단계적으로 설명이 필요한 경우 번호나 불릿을 활용해 가독성 있게 정리합니다.
        - 민감하거나 부적절한 요청이 들어오면 안전한 방향으로 안내하고, 관련 정책을 준수합니다.
        - 사용자의 목표 달성을 돕기 위해 추가로 도움이 될만한 정보를 제안할 수 있습니다.
        """;

    private final StrategyRepository strategyRepository;
    private final LlmKeyRepository llmKeyRepository;
    private final AgentPromptRepository agentPromptRepository;
    private final List<LlmChatClient> clients;
    private final OpenAiProperties openAiProperties;
    private final GeminiProperties geminiProperties;
    private final AnthropicProperties anthropicProperties;
    private final RunpodProperties runpodProperties;


    private AgentPrompt agentPrompt;

    @PostConstruct
    private void init() {
        agentPrompt = agentPromptRepository.findByNameIgnoreCase(PROMPT_NAME)
            .orElseGet(() -> {
                AgentPrompt created = AgentPrompt.builder()
                    .name(PROMPT_NAME)
                    .content(PROMPT_FALLBACK)
                    .llm(null)
                    .build();
                return agentPromptRepository.save(Objects.requireNonNull(created));
            });
    }

    public LlmChatResult chat(UUID userNo, UUID strategyNo, List<LlmChatMessage> messages) {
        if (userNo == null) {
            throw new BusinessException(ErrorCode.INVALID_INPUT);
        }
        return chatInternal(strategyNo, messages,
            (provider, strategy) -> resolveApiKey(userNo, provider, strategy));
    }

    public LlmChatResult streamChat(
        UUID userNo,
        UUID strategyNo,
        List<LlmChatMessage> messages,
        Consumer<String> onPartial
    ) {
        if (userNo == null) {
            throw new BusinessException(ErrorCode.INVALID_INPUT);
        }
        InvocationContext context = prepareInvocation(strategyNo, messages,
            (provider, strategy) -> resolveApiKey(userNo, provider, strategy));

        long startedAt = System.nanoTime();
        LlmChatResult result;
        LlmChatClient client = context.client();
        try {
            if (client instanceof StreamingLlmChatClient streamingClient) {
                result = streamingClient.stream(context.request(), onPartial);
            } else {
                result = client.chat(context.request());
                if (result != null && StringUtils.hasText(result.content()) && onPartial != null) {
                    onPartial.accept(result.content());
                }
            }
        } catch (Exception ex) {
            logInvocationFailure(context, ex);
            throw ex;
        }
        long responseTimeMs = Duration.ofNanos(System.nanoTime() - startedAt).toMillis();

        if (result == null || !StringUtils.hasText(result.content())) {
            log.error("LLM 스트리밍 응답이 비어있습니다. provider={}, strategy={}",
                context.provider(), strategyNo);
            throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
        }

        String trimmedContent = result.content() != null ? result.content().strip() : null;
        Long effectiveResponseTime = result.responseTimeMs() != null
            ? result.responseTimeMs()
            : responseTimeMs;

        return new LlmChatResult(
            result.role(),
            trimmedContent,
            result.inputTokens(),
            result.outputTokens(),
            result.totalTokens(),
            effectiveResponseTime
        );
    }

    public LlmChatResult chatWithSystem(UUID strategyNo, List<LlmChatMessage> messages) {
        return chatInternal(strategyNo, messages, this::resolveSystemApiKey);
    }

    private boolean containsSystemMessage(List<LlmChatMessage> messages) {
        return messages.stream()
            .anyMatch(message -> "system".equalsIgnoreCase(message.role()));
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

    private Optional<String> resolveSystemPrompt(UUID llmNo) {
        Optional<String> savedPrompt = Optional.empty();
        if (llmNo != null) {
            savedPrompt = agentPromptRepository
                .findByNameIgnoreCase(PROMPT_NAME)
                .map(AgentPrompt::getContent)
                .filter(StringUtils::hasText);
        }

        if (savedPrompt.isEmpty()) {
            savedPrompt = agentPromptRepository.findByNameIgnoreCase(PROMPT_NAME)
            .map(AgentPrompt::getContent)
            .filter(StringUtils::hasText);
        }

        if (savedPrompt.isPresent()) {
            return savedPrompt;
        }

        return Optional.of(PROMPT_FALLBACK);
    }

    private String resolveApiKey(UUID userNo, LlmProvider provider, Strategy strategy) {
        Optional<String> userKey = llmKeyRepository
            .findByUserUuidAndStrategyNo(userNo, strategy.getStrategyNo())
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

    private String resolveSystemApiKey(LlmProvider provider, Strategy strategy) {
        Optional<String> systemKey = llmKeyRepository
            .findSystemLlmKeyByStrategyNo(strategy.getStrategyNo())
            .map(LlmKey::getApiKey)
            .filter(StringUtils::hasText);

        if (systemKey.isPresent()) {
            return systemKey.get();
        }

        String fallback = fallbackApiKey(provider, strategy);
        if (StringUtils.hasText(fallback)) {
            log.warn("시스템용 LLM 키를 찾지 못해 기본 키를 사용합니다. provider={}, strategy={}",
                provider, strategy.getStrategyNo());
            return fallback;
        }

        log.error("시스템용 LLM 키가 존재하지 않습니다. provider={}, strategy={}",
            provider, strategy.getStrategyNo());
        throw new BusinessException(ErrorCode.NOT_FOUND);
    }

    private LlmChatResult chatInternal(
        UUID strategyNo,
        List<LlmChatMessage> messages,
        BiFunction<LlmProvider, Strategy, String> apiKeyResolver
    ) {
        InvocationContext context = prepareInvocation(strategyNo, messages, apiKeyResolver);
        long startedAt = System.nanoTime();
        LlmChatResult result;
        try {
            result = context.client().chat(context.request());
        } catch (Exception ex) {
            logInvocationFailure(context, ex);
            throw ex;
        }
        long responseTimeMs = Duration.ofNanos(System.nanoTime() - startedAt).toMillis();

        if (result == null || !StringUtils.hasText(result.content())) {
            log.error("LLM 응답이 비어있습니다. provider={}, strategy={}",
                context.provider(), context.strategy().getStrategyNo());
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

    private void logInvocationFailure(InvocationContext context, Exception ex) {
        Strategy strategy = context.strategy();
        log.error("LLM 호출 실패 - provider={}, strategyNo={}, strategyCode={}, strategyName={}",
            context.provider(),
            strategy != null ? strategy.getStrategyNo() : null,
            strategy != null ? strategy.getCode() : null,
            strategy != null ? strategy.getName() : null,
            ex);
    }

    private InvocationContext prepareInvocation(
        UUID strategyNo,
        List<LlmChatMessage> messages,
        BiFunction<LlmProvider, Strategy, String> apiKeyResolver
    ) {
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

        String apiKey = apiKeyResolver.apply(provider, strategy);
        String model = resolveModel(provider, strategy);
        JsonNode parameter = strategy.getParameter();

        UUID llmNo = strategy.getStrategyNo();

        List<LlmChatMessage> payloadMessages = new ArrayList<>();
        if (!containsSystemMessage(messages)) {
            String systemPrompt = agentPrompt.getContent();
            if (StringUtils.hasText(systemPrompt)) {
                payloadMessages.add(new LlmChatMessage("system", systemPrompt));
            }
        }
        payloadMessages.addAll(messages);

        LlmChatRequest request = new LlmChatRequest(
            provider,
            model,
            apiKey,
            payloadMessages,
            parameter,
            strategy.getName(),
            strategy.getCode()
        );

        return new InvocationContext(strategy, provider, client, request);
    }

    private record InvocationContext(
        Strategy strategy,
        LlmProvider provider,
        LlmChatClient client,
        LlmChatRequest request
    ) {
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

