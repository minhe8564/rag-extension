package com.ssafy.hebees.monitoring.client;

import com.fasterxml.jackson.databind.JsonNode;
import lombok.NoArgsConstructor;
import lombok.extern.slf4j.Slf4j;

import java.time.Instant;
import java.time.OffsetDateTime;
import java.time.format.DateTimeParseException;

/**
 * cAdvisor JSON 응답 파싱 유틸리티
 */
@Slf4j
@NoArgsConstructor
public class CadvisorJsonUtils {

    /**
     * JSON 노드에서 텍스트 필드 추출
     */
    public static String text(JsonNode node, String field) {
        JsonNode value = node == null ? null : node.get(field);
        return value != null && value.isTextual() ? value.asText() : null;
    }

    /**
     * JSON 노드에서 Long 숫자 필드 추출
     */
    public static Long number(JsonNode node, String field) {
        JsonNode value = node == null ? null : node.get(field);
        return value != null && value.isNumber() ? value.longValue() : null;
    }

    /**
     * JSON 노드에서 Double 숫자 필드 추출
     */
    public static Double numberDouble(JsonNode node, String field) {
        JsonNode value = node == null ? null : node.get(field);
        return value != null && value.isNumber() ? value.doubleValue() : null;
    }

    /**
     * JSON 문자열을 Instant로 변환
     */
    public static Instant parseTimestamp(String raw) {
        if (raw == null || raw.isBlank()) {
            return null;
        }
        try {
            return OffsetDateTime.parse(raw).toInstant();
        } catch (DateTimeParseException ex) {
            log.debug("Failed to parse cAdvisor timestamp '{}': {}", raw, ex.getMessage());
            return null;
        }
    }
}

