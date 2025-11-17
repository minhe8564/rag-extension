package com.ssafy.hebees.chat.client;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.ssafy.hebees.chat.client.dto.LlmChatMessage;
import com.ssafy.hebees.chat.client.dto.LlmChatRequest;
import com.ssafy.hebees.chat.client.dto.LlmChatResult;
import com.ssafy.hebees.chat.config.OpenAiProperties;
import com.ssafy.hebees.common.exception.BusinessException;
import com.ssafy.hebees.common.exception.ErrorCode;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicReference;
import java.util.function.Consumer;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;
import org.springframework.util.CollectionUtils;
import org.springframework.util.StringUtils;
import org.springframework.util.StreamUtils;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.util.UriComponentsBuilder;

@Slf4j
@Component
@RequiredArgsConstructor
public class OpenAiChatClient implements StreamingLlmChatClient {

    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper;
    private final OpenAiProperties properties;

    @Override
    public boolean supports(LlmProvider provider) {
        return provider == LlmProvider.CHATGPT;
    }

    private void validateMessages(List<LlmChatMessage> messages, String strategyCode) {
        if (CollectionUtils.isEmpty(messages)) {
            log.error("OpenAI 요청에 사용할 메시지가 없습니다. strategy={}", strategyCode);
            throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
        }
    }

    private String resolveApiKey(LlmChatRequest request) {
        String apiKey = request.apiKey();
        if (!StringUtils.hasText(apiKey)) {
            log.error("OpenAI API 키가 설정되지 않았습니다. strategy={}", request.strategyCode());
            throw new BusinessException(ErrorCode.NOT_FOUND);
        }
        return apiKey;
    }

    private String resolveEndpoint(LlmChatRequest request) {
        String baseUrl = resolveBaseUrl(request);
        String path = StringUtils.hasText(properties.getChatPath()) ? properties.getChatPath()
            : "/v1/chat/completions";

        return UriComponentsBuilder.fromUriString(Objects.requireNonNull(baseUrl))
            .path(Objects.requireNonNull(path))
            .toUriString();
    }

    private ObjectNode buildPayload(LlmChatRequest request, boolean streamEnabled) {
        ObjectNode payload = objectMapper.createObjectNode();
        payload.put("model", resolveModel(request));

        Double temperature = resolveDouble(request.parameter(), "temperature")
            .orElse(properties.getDefaultTemperature());
        if (temperature != null) {
            payload.put("temperature", temperature);
        }

        Integer maxTokens = resolveInt(request.parameter(), "maxTokens")
            .orElse(properties.getDefaultMaxTokens());
        if (maxTokens != null) {
            payload.put("max_tokens", maxTokens);
        }

        ArrayNode messagesNode = payload.putArray("messages");
        populateMessages(messagesNode, request.messages(), request.strategyCode());

        applyOptionalArray(payload, request.parameter(), "responseFormat", "response_format");

        if (streamEnabled) {
            payload.put("stream", true);
        }

        return payload;
    }

    private void populateMessages(ArrayNode target, List<LlmChatMessage> messages,
        String strategyCode) {
        boolean hasMessage = false;
        for (LlmChatMessage message : messages) {
            if (message == null || !StringUtils.hasText(message.content())) {
                continue;
            }
            ObjectNode messageNode = objectMapper.createObjectNode();
            messageNode.put("role", normalizeRole(message.role()));
            messageNode.put("content", message.content());
            target.add(messageNode);
            hasMessage = true;
        }

        if (!hasMessage) {
            log.error("OpenAI 요청 메시지가 비어있습니다. strategy={}", strategyCode);
            throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
        }
    }

    private boolean processStreamEvent(
        StringBuilder eventBuffer,
        String strategyCode,
        AtomicReference<String> roleRef,
        StringBuilder contentBuilder,
        AtomicReference<Long> inputTokens,
        AtomicReference<Long> outputTokens,
        AtomicReference<Long> totalTokens,
        Consumer<String> onPartial
    ) {
        if (eventBuffer == null || eventBuffer.length() == 0) {
            return true;
        }

        String data = eventBuffer.toString().trim();
        if (!StringUtils.hasText(data)) {
            return true;
        }

        if ("[DONE]".equals(data)) {
            return false;
        }

        try {
            JsonNode root = objectMapper.readTree(data);

            JsonNode errorNode = root.path("error");
            if (!errorNode.isMissingNode() && errorNode.isObject()) {
                log.error("OpenAI 스트리밍 응답 오류: {}", errorNode);
                throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
            }

            JsonNode choices = root.path("choices");
            if (choices.isArray() && !choices.isEmpty()) {
                JsonNode choice = choices.get(0);
                JsonNode delta = choice.path("delta");
                if (delta.has("role") && delta.path("role").isTextual()) {
                    roleRef.set(delta.path("role").asText("assistant"));
                }

                String contentFragment = null;
                if (delta.has("content") && delta.path("content").isTextual()) {
                    contentFragment = delta.path("content").asText();
                } else if (choice.path("message").has("content")
                    && choice.path("message").path("content").isTextual()) {
                    contentFragment = choice.path("message").path("content").asText();
                }

                if (StringUtils.hasText(contentFragment)) {
                    contentBuilder.append(contentFragment);
                    if (onPartial != null) {
                        onPartial.accept(contentFragment);
                    }
                }

                JsonNode finishReason = choice.path("finish_reason");
                if (finishReason.isTextual() && !Objects.equals(finishReason.asText(), "stop")) {
                    log.debug("OpenAI 스트리밍 finish_reason={}", finishReason.asText());
                }
            }

            JsonNode usage = root.path("usage");
            if (usage.isObject()) {
                inputTokens.set(extractLong(usage, "prompt_tokens"));
                outputTokens.set(extractLong(usage, "completion_tokens"));
                totalTokens.set(extractLong(usage, "total_tokens"));
            }

            return true;
        } catch (JsonProcessingException e) {
            log.error("OpenAI 스트리밍 이벤트 파싱 실패: {}", data, e);
            throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
        }
    }

    @Override
    public LlmChatResult chat(LlmChatRequest request) {
        List<LlmChatMessage> messages = request.messages();
        validateMessages(messages, request.strategyCode());

        String apiKey = resolveApiKey(request);
        String url = resolveEndpoint(request);
        ObjectNode payload = buildPayload(request, false);

        HttpHeaders headers = buildHeaders(apiKey, request.parameter());
        HttpEntity<String> entity = new HttpEntity<>(payload.toString(), headers);

        try {
            ResponseEntity<String> response = restTemplate.postForEntity(url, entity, String.class);
            if (!response.getStatusCode().is2xxSuccessful() || response.getBody() == null) {
                log.error("OpenAI 응답 실패: status={}, body={}", response.getStatusCode(),
                    response.getBody());
                throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
            }
            return parseResponse(response.getBody());
        } catch (RestClientException | JsonProcessingException e) {
            log.error("OpenAI API 호출 실패", e);
            throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
        }
    }

    @Override
    public LlmChatResult stream(LlmChatRequest request, Consumer<String> onPartial) {
        List<LlmChatMessage> messages = request.messages();
        validateMessages(messages, request.strategyCode());

        String apiKey = resolveApiKey(request);
        String url = resolveEndpoint(request);
        ObjectNode payload = buildPayload(request, true);

        HttpHeaders headers = buildHeaders(apiKey, request.parameter());
        headers.setAccept(List.of(MediaType.TEXT_EVENT_STREAM, MediaType.APPLICATION_JSON));
        String payloadString = payload.toString();

        AtomicReference<String> roleRef = new AtomicReference<>("assistant");
        AtomicReference<Long> inputTokens = new AtomicReference<>(null);
        AtomicReference<Long> outputTokens = new AtomicReference<>(null);
        AtomicReference<Long> totalTokens = new AtomicReference<>(null);
        StringBuilder contentBuilder = new StringBuilder();

        try {
            restTemplate.execute(url, HttpMethod.POST, clientHttpRequest -> {
                clientHttpRequest.getHeaders().putAll(headers);
                try (OutputStream body = clientHttpRequest.getBody()) {
                    StreamUtils.copy(payloadString, StandardCharsets.UTF_8, body);
                } catch (IOException ioException) {
                    log.error("OpenAI 스트리밍 요청 전송 실패", ioException);
                    throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
                }
            }, clientHttpResponse -> {
                if (!clientHttpResponse.getStatusCode().is2xxSuccessful()) {
                    log.error("OpenAI 스트리밍 응답 실패: status={}",
                        clientHttpResponse.getStatusCode());
                    throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
                }
                try (BufferedReader reader = new BufferedReader(
                    new InputStreamReader(clientHttpResponse.getBody(), StandardCharsets.UTF_8))) {
                    String line;
                    StringBuilder eventBuffer = new StringBuilder();
                    while ((line = reader.readLine()) != null) {
                        if (line.startsWith("data:")) {
                            eventBuffer.append(line.substring(5).trim());
                        } else if (line.isEmpty()) {
                            if (!processStreamEvent(
                                eventBuffer,
                                request.strategyCode(),
                                roleRef,
                                contentBuilder,
                                inputTokens,
                                outputTokens,
                                totalTokens,
                                onPartial)) {
                                break;
                            }
                            eventBuffer.setLength(0);
                        }
                    }
                    if (eventBuffer.length() > 0) {
                        processStreamEvent(
                            eventBuffer,
                            request.strategyCode(),
                            roleRef,
                            contentBuilder,
                            inputTokens,
                            outputTokens,
                            totalTokens,
                            onPartial);
                    }
                } catch (IOException ex) {
                    log.error("OpenAI 스트리밍 응답 처리 중 오류 발생", ex);
                    throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
                }
                return null;
            });
        } catch (RestClientException e) {
            log.error("OpenAI 스트리밍 API 호출 실패", e);
            throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
        }

        String finalContent = contentBuilder.toString();
        if (!StringUtils.hasText(finalContent)) {
            log.error("OpenAI 스트리밍 응답이 비어있습니다. strategy={}", request.strategyCode());
            throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
        }

        return new LlmChatResult(
            roleRef.get(),
            finalContent,
            inputTokens.get(),
            outputTokens.get(),
            totalTokens.get(),
            null
        );
    }

    private String resolveBaseUrl(LlmChatRequest request) {
        String override = extractText(request.parameter(), "baseUrl");
        if (StringUtils.hasText(override)) {
            return override;
        }
        if (StringUtils.hasText(properties.getBaseUrl())) {
            return properties.getBaseUrl();
        }
        log.error("OpenAI base URL을 확인할 수 없습니다. strategy={}", request.strategyCode());
        throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
    }

    private String resolveModel(LlmChatRequest request) {
        if (StringUtils.hasText(request.model())) {
            return request.model();
        }
        String override = extractText(request.parameter(), "model");
        if (StringUtils.hasText(override)) {
            return override;
        }
        if (StringUtils.hasText(properties.getDefaultModel())) {
            return properties.getDefaultModel();
        }
        log.error("OpenAI 모델이 설정되지 않았습니다. strategy={}", request.strategyCode());
        throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
    }

    private LlmChatResult parseResponse(String body)
        throws JsonProcessingException {
        JsonNode root = objectMapper.readTree(body);
        JsonNode choices = root.path("choices");
        if (!choices.isArray() || choices.isEmpty()) {
            log.error("OpenAI 응답에 choices가 없습니다: {}", body);
            throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
        }

        JsonNode message = choices.get(0).path("message");
        String content = message.path("content").asText(null);
        String role = message.path("role").asText("assistant");

        if (!StringUtils.hasText(content)) {
            log.error("OpenAI 응답 content가 비어있습니다: {}", body);
            throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
        }

        JsonNode usage = root.path("usage");
        Long inputTokens = extractLong(usage, "prompt_tokens");
        Long outputTokens = extractLong(usage, "completion_tokens");
        Long totalTokens = extractLong(usage, "total_tokens");

        return new LlmChatResult(role, content, inputTokens, outputTokens, totalTokens, null);
    }

    private HttpHeaders buildHeaders(String apiKey, JsonNode parameter) {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        headers.setBearerAuth(Objects.requireNonNull(apiKey));

        String organization = extractText(parameter, "organization");
        if (!StringUtils.hasText(organization)) {
            organization = properties.getOrganization();
        }
        if (StringUtils.hasText(organization)) {
            headers.set("OpenAI-Organization", Objects.requireNonNull(organization));
        }

        return headers;
    }

    private String normalizeRole(String role) {
        if (!StringUtils.hasText(role)) {
            return "user";
        }
        String normalized = role.strip().toLowerCase();
        return switch (normalized) {
            case "human", "user" -> "user";
            case "assistant", "ai" -> "assistant";
            case "system" -> "system";
            case "tool" -> "tool";
            default -> "user";
        };
    }

    private String extractText(JsonNode node, String path) {
        if (node == null || !StringUtils.hasText(path)) {
            return null;
        }
        JsonNode value = node.path(path);
        return value.isTextual() ? value.asText() : null;
    }

    private Long extractLong(JsonNode node, String path) {
        if (node == null || !StringUtils.hasText(path)) {
            return null;
        }
        JsonNode value = node.path(path);
        if (value.isIntegralNumber()) {
            return value.asLong();
        }
        return null;
    }

    private Optional<Double> resolveDouble(JsonNode node, String name) {
        if (node == null) {
            return Optional.empty();
        }
        JsonNode value = node.path(name);
        if (value.isNumber()) {
            return Optional.of(value.asDouble());
        }
        return Optional.empty();
    }

    private Optional<Integer> resolveInt(JsonNode node, String name) {
        if (node == null) {
            return Optional.empty();
        }
        JsonNode value = node.path(name);
        if (value.isInt() || value.isLong()) {
            return Optional.of(value.asInt());
        }
        return Optional.empty();
    }

    private void applyOptionalArray(ObjectNode payload, JsonNode parameter, String sourceField,
        String targetField) {
        if (parameter == null || !StringUtils.hasText(sourceField) || !StringUtils.hasText(
            targetField)) {
            return;
        }
        JsonNode source = parameter.path(sourceField);
        if (source.isArray() && source.size() > 0) {
            payload.set(targetField, source);
        }
    }
}

