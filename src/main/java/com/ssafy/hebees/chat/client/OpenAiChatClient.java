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
import java.util.List;
import java.util.Objects;
import java.util.Optional;
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
public class OpenAiChatClient implements LlmChatClient {

    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper;
    private final OpenAiProperties properties;

    @Override
    public boolean supports(LlmProvider provider) {
        return provider == LlmProvider.CHATGPT;
    }

    @Override
    public LlmChatResult chat(LlmChatRequest request) {
        List<LlmChatMessage> messages = request.messages();
        if (CollectionUtils.isEmpty(messages)) {
            log.error("OpenAI 요청에 사용할 메시지가 없습니다. strategy={}", request.strategyCode());
            throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
        }

        String apiKey = request.apiKey();
        if (!StringUtils.hasText(apiKey)) {
            log.error("OpenAI API 키가 설정되지 않았습니다. strategy={}", request.strategyCode());
            throw new BusinessException(ErrorCode.NOT_FOUND);
        }

        String baseUrl = resolveBaseUrl(request);
        String path = StringUtils.hasText(properties.getChatPath()) ? properties.getChatPath()
            : "/v1/chat/completions";

        String url = UriComponentsBuilder.fromUriString(Objects.requireNonNull(baseUrl))
            .path(Objects.requireNonNull(path))
            .toUriString();

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
        for (LlmChatMessage message : messages) {
            if (message == null || !StringUtils.hasText(message.content())) {
                continue;
            }
            ObjectNode messageNode = objectMapper.createObjectNode();
            messageNode.put("role", normalizeRole(message.role()));
            messageNode.put("content", message.content());
            messagesNode.add(messageNode);
        }

        if (messagesNode.isEmpty()) {
            log.error("OpenAI 요청 메시지가 비어있습니다. strategy={}", request.strategyCode());
            throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
        }

        applyOptionalArray(payload, request.parameter(), "responseFormat", "response_format");

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

