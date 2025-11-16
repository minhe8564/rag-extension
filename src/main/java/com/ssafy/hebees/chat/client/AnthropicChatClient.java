package com.ssafy.hebees.chat.client;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.ssafy.hebees.chat.client.dto.LlmChatMessage;
import com.ssafy.hebees.chat.client.dto.LlmChatRequest;
import com.ssafy.hebees.chat.client.dto.LlmChatResult;
import com.ssafy.hebees.chat.config.AnthropicProperties;
import com.ssafy.hebees.common.exception.BusinessException;
import com.ssafy.hebees.common.exception.ErrorCode;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.stream.Collectors;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;
import org.springframework.util.CollectionUtils;
import org.springframework.util.StringUtils;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.util.UriComponentsBuilder;

@Slf4j
@Component
@RequiredArgsConstructor
public class AnthropicChatClient implements LlmChatClient {

    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper;
    private final AnthropicProperties properties;

    @Override
    public boolean supports(LlmProvider provider) {
        return provider == LlmProvider.CLAUDE;
    }

    @Override
    public LlmChatResult chat(LlmChatRequest request) {
        List<LlmChatMessage> messages = request.messages();
        if (CollectionUtils.isEmpty(messages)) {
            log.error("Anthropic 요청 메시지가 비어있습니다. strategy={}", request.strategyCode());
            throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
        }

        String apiKey = request.apiKey();
        if (!StringUtils.hasText(apiKey)) {
            log.error("Anthropic API 키가 설정되지 않았습니다. strategy={}", request.strategyCode());
            throw new BusinessException(ErrorCode.NOT_FOUND);
        }

        String baseUrl = resolveBaseUrl(request);
        String path =
            StringUtils.hasText(properties.getMessagesPath()) ? properties.getMessagesPath()
                : "/v1/messages";

        String url = UriComponentsBuilder.fromUriString(Objects.requireNonNull(baseUrl))
            .path(Objects.requireNonNull(path))
            .toUriString();

        ObjectNode payload = objectMapper.createObjectNode();
        payload.put("model", resolveModel(request));
        payload.put("max_tokens", resolveMaxTokens(request.parameter()));

        Double temperature = resolveDouble(request.parameter(), "temperature")
            .orElse(properties.getDefaultTemperature());
        if (temperature != null) {
            payload.put("temperature", temperature);
        }

        String systemPrompt = extractSystemPrompt(messages);
        if (StringUtils.hasText(systemPrompt)) {
            payload.put("system", systemPrompt);
        }

        ArrayNode messageArray = payload.putArray("messages");
        for (LlmChatMessage message : messages) {
            if (message == null || !StringUtils.hasText(message.content())) {
                continue;
            }

            String normalizedRole = normalizeRole(message.role());
            if ("system".equals(normalizedRole)) {
                continue;
            }

            ObjectNode messageNode = objectMapper.createObjectNode();
            messageNode.put("role", normalizedRole);
            ArrayNode contentArray = messageNode.putArray("content");

            ObjectNode textNode = objectMapper.createObjectNode();
            textNode.put("type", "text");
            textNode.put("text", message.content());
            contentArray.add(textNode);

            messageArray.add(messageNode);
        }

        if (messageArray.isEmpty()) {
            log.error("Anthropic 메시지 배열이 비어있습니다. strategy={}", request.strategyCode());
            throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
        }

        HttpHeaders headers = buildHeaders(apiKey);
        HttpEntity<String> entity = new HttpEntity<>(payload.toString(), headers);

        try {
            ResponseEntity<String> response = restTemplate.postForEntity(url, entity, String.class);
            if (!response.getStatusCode().is2xxSuccessful() || response.getBody() == null) {
                log.error("Anthropic 응답 실패: status={}, body={}",
                    response.getStatusCode(), response.getBody());
                throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
            }
            return parseResponse(response.getBody());
        } catch (RestClientException | JsonProcessingException e) {
            log.error("Anthropic API 호출 실패", e);
            throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
        }
    }

    private String resolveBaseUrl(LlmChatRequest request) {
        String override = extractText(request.parameter(), "baseUrl");
        if (StringUtils.hasText(override)) {
            return override;
        }
        if (StringUtils.hasText(properties.getBaseUrl())) {
            return properties.getBaseUrl();
        }
        log.error("Anthropic base URL을 확인할 수 없습니다. strategy={}", request.strategyCode());
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
        log.error("Anthropic 모델이 설정되지 않았습니다. strategy={}", request.strategyCode());
        throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
    }

    private int resolveMaxTokens(JsonNode parameter) {
        return resolveInt(parameter, "maxTokens")
            .orElse(Optional.ofNullable(properties.getDefaultMaxTokens()).orElse(1024));
    }

    private HttpHeaders buildHeaders(String apiKey) {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        headers.set("x-api-key", apiKey);
        headers.set("anthropic-version", resolveApiVersion());
        return headers;
    }

    private String resolveApiVersion() {
        if (StringUtils.hasText(properties.getApiVersion())) {
            return properties.getApiVersion();
        }
        return "2023-06-01";
    }

    private LlmChatResult parseResponse(String body) throws JsonProcessingException {
        JsonNode root = objectMapper.readTree(body);
        JsonNode contentArray = root.path("content");
        if (!contentArray.isArray() || contentArray.isEmpty()) {
            log.error("Anthropic 응답 content가 비어있습니다: {}", body);
            throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
        }

        JsonNode first = contentArray.get(0);
        String text = first.path("text").asText(null);
        if (!StringUtils.hasText(text)) {
            log.error("Anthropic 응답 text가 없습니다: {}", body);
            throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
        }

        JsonNode usage = root.path("usage");
        Long inputTokens = extractLong(usage, "input_tokens");
        Long outputTokens = extractLong(usage, "output_tokens");
        Long totalTokens = null;
        if (inputTokens != null || outputTokens != null) {
            totalTokens = Optional.ofNullable(inputTokens).orElse(0L)
                + Optional.ofNullable(outputTokens).orElse(0L);
        }

        return new LlmChatResult("assistant", text, inputTokens, outputTokens, totalTokens, null);
    }

    private String extractSystemPrompt(List<LlmChatMessage> messages) {
        if (CollectionUtils.isEmpty(messages)) {
            return null;
        }
        return messages.stream()
            .filter(message -> "system".equalsIgnoreCase(message.role()))
            .map(LlmChatMessage::content)
            .filter(StringUtils::hasText)
            .collect(Collectors.joining("\n"));
    }

    private String normalizeRole(String role) {
        if (!StringUtils.hasText(role)) {
            return "user";
        }
        return switch (role.strip().toLowerCase()) {
            case "assistant", "ai" -> "assistant";
            case "system" -> "system";
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

    private Long extractLong(JsonNode node, String fieldName) {
        if (node == null || !StringUtils.hasText(fieldName)) {
            return null;
        }
        JsonNode value = node.path(fieldName);
        if (value.isIntegralNumber()) {
            return value.asLong();
        }
        return null;
    }
}

