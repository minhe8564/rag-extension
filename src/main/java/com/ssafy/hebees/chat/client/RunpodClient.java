package com.ssafy.hebees.chat.client;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.ssafy.hebees.chat.client.dto.RunpodChatMessage;
import com.ssafy.hebees.chat.client.dto.RunpodChatRequest;
import com.ssafy.hebees.chat.client.dto.RunpodChatResult;
import com.ssafy.hebees.chat.config.RunpodProperties;
import com.ssafy.hebees.common.exception.BusinessException;
import com.ssafy.hebees.common.exception.ErrorCode;
import java.util.ArrayList;
import java.util.List;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.util.UriComponentsBuilder;

@Slf4j
@Component
@RequiredArgsConstructor
public class RunpodClient {

    private static final String CHAT_PATH = "/api/chat";

    private final RestTemplate restTemplate;
    private final RunpodProperties properties;
    private final ObjectMapper objectMapper;

    public RunpodChatResult chat(List<RunpodChatMessage> messages) {
        String baseUrl = properties.getBaseUrl();
        if (!StringUtils.hasText(baseUrl)) {
            log.error("Runpod base URL is not configured");
            throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
        }

        String model = properties.getModel();
        if (!StringUtils.hasText(model)) {
            log.error("Runpod model is not configured");
            throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
        }

        String url = UriComponentsBuilder.fromHttpUrl(baseUrl)
            .path(CHAT_PATH)
            .toUriString();

        RunpodChatRequest payload = RunpodChatRequest.of(model, messages);

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);

        HttpEntity<RunpodChatRequest> entity = new HttpEntity<>(payload, headers);

        try {
            ResponseEntity<String> response = restTemplate.postForEntity(url, entity, String.class);
            if (!response.getStatusCode().is2xxSuccessful() || response.getBody() == null) {
                log.error("Runpod chat request failed: status={}, body={}",
                    response.getStatusCode(), response.getBody());
                throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
            }

            return parseResponse(response.getBody());
        } catch (RestClientException | JsonProcessingException e) {
            log.error("Failed to call Runpod chat API", e);
            throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
        }
    }

    private RunpodChatResult parseResponse(String body) throws JsonProcessingException {
        JsonNode root = objectMapper.readTree(body);
        JsonNode messageNode = root.path("message");
        if (messageNode.isMissingNode() || messageNode.isNull()) {
            log.error("Runpod response missing message node: {}", body);
            throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
        }

        String role = messageNode.path("role").asText("assistant");
        String content = extractContent(messageNode.path("content"));

        if (!StringUtils.hasText(content)) {
            log.error("Runpod response content is empty: {}", body);
            throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
        }

        return new RunpodChatResult(role, content);
    }

    private String extractContent(JsonNode contentNode) {
        if (contentNode.isNull() || contentNode.isMissingNode()) {
            return null;
        }

        if (contentNode.isTextual()) {
            return contentNode.asText();
        }

        if (contentNode.isObject()) {
            JsonNode textNode = contentNode.path("text");
            return textNode.isTextual() ? textNode.asText() : null;
        }

        if (contentNode.isArray()) {
            List<String> parts = new ArrayList<>();
            for (JsonNode node : contentNode) {
                String part = extractContent(node);
                if (StringUtils.hasText(part)) {
                    parts.add(part);
                }
            }
            return String.join("\n", parts);
        }

        return null;
    }
}
