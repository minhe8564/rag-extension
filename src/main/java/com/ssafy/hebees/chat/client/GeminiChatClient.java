package com.ssafy.hebees.chat.client;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.ssafy.hebees.chat.client.dto.LlmChatMessage;
import com.ssafy.hebees.chat.client.dto.LlmChatRequest;
import com.ssafy.hebees.chat.client.dto.LlmChatResult;
import com.ssafy.hebees.chat.config.GeminiProperties;
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
public class GeminiChatClient implements LlmChatClient {

    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper;
    private final GeminiProperties properties;

    @Override
    public boolean supports(LlmProvider provider) {
        return provider == LlmProvider.GEMINI;
    }

    @Override
    public LlmChatResult chat(LlmChatRequest request) {
        List<LlmChatMessage> messages = request.messages();
        if (CollectionUtils.isEmpty(messages)) {
            log.error("Gemini 요청 메시지가 비어있습니다. strategy={}", request.strategyCode());
            throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
        }

        String apiKey = request.apiKey();
        if (!StringUtils.hasText(apiKey)) {
            log.error("Gemini API 키가 설정되지 않았습니다. strategy={}", request.strategyCode());
            throw new BusinessException(ErrorCode.NOT_FOUND);
        }

        String model = resolveModel(request);
        String baseUrl = resolveBaseUrl(request);
        String version = StringUtils.hasText(properties.getVersion()) ? properties.getVersion()
            : "v1beta";

        String url = String.format("%s/%s/models/%s:generateContent", baseUrl, version, model);
        UriComponentsBuilder builder = UriComponentsBuilder.fromUriString(Objects.requireNonNull(url))
            .queryParam("key", apiKey);

        ObjectNode payload = objectMapper.createObjectNode();

        String systemPrompt = extractSystemPrompt(messages);
        if (StringUtils.hasText(systemPrompt)) {
            ObjectNode systemInstruction = objectMapper.createObjectNode();
            ArrayNode systemParts = systemInstruction.putArray("parts");
            ObjectNode part = objectMapper.createObjectNode();
            part.put("text", systemPrompt);
            systemParts.add(part);
            payload.set("systemInstruction", systemInstruction);
            payload.set("system_instruction", systemInstruction);
        }

        ArrayNode contents = payload.putArray("contents");
        for (LlmChatMessage message : messages) {
            if (!StringUtils.hasText(message.content())) {
                continue;
            }
            String normalizedRole = normalizeRole(message.role());
            if ("system".equals(normalizedRole)) {
                continue;
            }
            ObjectNode contentNode = objectMapper.createObjectNode();
            contentNode.put("role", normalizedRole);
            ArrayNode parts = contentNode.putArray("parts");
            ObjectNode textPart = objectMapper.createObjectNode();
            textPart.put("text", message.content());
            parts.add(textPart);
            contents.add(contentNode);
        }

        if (contents.isEmpty()) {
            log.error("Gemini 요청 contents가 비어있습니다. strategy={}", request.strategyCode());
            throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
        }

        ObjectNode generationConfig = buildGenerationConfig(request.parameter());
        if (!generationConfig.isEmpty()) {
            payload.set("generationConfig", generationConfig);
        }

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);

        HttpEntity<String> entity = new HttpEntity<>(payload.toString(), headers);

        try {
            ResponseEntity<String> response =
                restTemplate.postForEntity(builder.toUriString(), entity, String.class);
            if (!response.getStatusCode().is2xxSuccessful() || response.getBody() == null) {
                log.error("Gemini 응답 실패: status={}, body={}",
                    response.getStatusCode(), response.getBody());
                throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
            }

            return parseResponse(response.getBody());
        } catch (RestClientException | JsonProcessingException e) {
            log.error("Gemini API 호출 실패", e);
            throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
        }
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
        log.error("Gemini 모델이 설정되지 않았습니다. strategy={}", request.strategyCode());
        throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
    }

    private String resolveBaseUrl(LlmChatRequest request) {
        String override = extractText(request.parameter(), "baseUrl");
        if (StringUtils.hasText(override)) {
            return override;
        }
        if (StringUtils.hasText(properties.getBaseUrl())) {
            return properties.getBaseUrl();
        }
        log.error("Gemini base URL을 확인할 수 없습니다. strategy={}", request.strategyCode());
        throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
    }

    private ObjectNode buildGenerationConfig(JsonNode parameter) {
        ObjectNode config = objectMapper.createObjectNode();
        Double temperature = resolveDouble(parameter, "temperature")
            .orElse(properties.getDefaultTemperature());
        if (temperature != null) {
            config.put("temperature", temperature);
        }

        resolveDouble(parameter, "topP").ifPresent(value -> config.put("topP", value));
        resolveDouble(parameter, "topK").ifPresent(value -> config.put("topK", value));
        Integer maxTokens = resolveInt(parameter, "maxOutputTokens")
            .orElse(properties.getDefaultMaxOutputTokens());
        if (maxTokens != null) {
            config.put("maxOutputTokens", maxTokens);
        }
        return config;
    }

    private LlmChatResult parseResponse(String body) throws JsonProcessingException {
        JsonNode root = objectMapper.readTree(body);
        JsonNode candidates = root.path("candidates");
        if (!candidates.isArray() || candidates.isEmpty()) {
            log.error("Gemini 응답 candidates가 비어있습니다: {}", body);
            throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
        }

        JsonNode content = candidates.get(0).path("content");
        JsonNode parts = content.path("parts");
        if (!parts.isArray() || parts.isEmpty()) {
            log.error("Gemini 응답 parts가 비어있습니다: {}", body);
            throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
        }

        JsonNode firstPart = parts.get(0);
        String text = firstPart.path("text").asText(null);
        if (!StringUtils.hasText(text)) {
            log.error("Gemini 응답 text가 없습니다: {}", body);
            throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
        }

        JsonNode usageMetadata = root.path("usageMetadata");
        Long inputTokens = extractLong(usageMetadata, "promptTokenCount");
        Long outputTokens = extractLong(usageMetadata, "candidatesTokenCount");
        Long totalTokens = extractLong(usageMetadata, "totalTokenCount");

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
            .findFirst()
            .orElse(null);
    }

    private String normalizeRole(String role) {
        if (!StringUtils.hasText(role)) {
            return "user";
        }
        return switch (role.strip().toLowerCase()) {
            case "assistant", "model", "ai" -> "model";
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

