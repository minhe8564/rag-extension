package com.ssafy.hebees.monitoring.client;

import com.fasterxml.jackson.databind.JsonNode;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * cAdvisor API 클라이언트 컨테이너 메트릭을 cAdvisor로부터 조회
 */
@Slf4j
@Component
public class CadvisorClient {

    private final RestTemplate restTemplate;
    private final String cadvisorBaseUrl;

    public CadvisorClient(
        RestTemplate restTemplate,
        @Value("${monitoring.cadvisor.base-url:http://localhost:8080}") String cadvisorBaseUrl
    ) {
        this.restTemplate = restTemplate;
        this.cadvisorBaseUrl = trimTrailingSlash(cadvisorBaseUrl);
    }

    private String getCadvisorBaseUrl() {
        return cadvisorBaseUrl;
    }

    /**
     * cAdvisor로부터 컨테이너 스냅샷 조회
     */
    public CadvisorSnapshot fetchSnapshot() {
        JsonNode containerRoot = fetchContainersNode();
        long machineMemoryBytes = fetchMachineMemoryBytes();

        if (containerRoot == null || containerRoot.isMissingNode()) {
            log.warn("cAdvisor returned no container payload.");
            return CadvisorSnapshot.empty(machineMemoryBytes);
        }

        List<CadvisorContainerMetrics> containers = new ArrayList<>();
        containerRoot.fields().forEachRemaining(entry -> {
            CadvisorContainerMetrics metrics = CadvisorMetricsParser.parseMetrics(
                entry.getValue(), machineMemoryBytes);
            if (metrics != null) {
                containers.add(metrics);
            }
        });

        return new CadvisorSnapshot(Collections.unmodifiableList(containers), machineMemoryBytes);
    }

    /**
     * 컨테이너 정보 조회
     */
    private JsonNode fetchContainersNode() {
        String url = getCadvisorBaseUrl() + "/api/v1.3/docker";
        try {
            ResponseEntity<JsonNode> response = restTemplate.getForEntity(url, JsonNode.class);
            return response.getStatusCode().is2xxSuccessful() ? response.getBody() : null;
        } catch (RestClientException ex) {
            log.warn("Failed to call cAdvisor at {}: {}", url, ex.getMessage());
            return null;
        }
    }

    /**
     * 머신 메모리 용량 조회
     */
    private long fetchMachineMemoryBytes() {
        String url = getCadvisorBaseUrl() + "/api/v1.3/machine";
        try {
            ResponseEntity<JsonNode> response = restTemplate.getForEntity(url, JsonNode.class);
            if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                JsonNode capacity = response.getBody().path("memory_capacity");
                if (capacity.isNumber()) {
                    return capacity.longValue();
                }
            }
        } catch (RestClientException ex) {
            log.warn("Failed to read cAdvisor machine info from {}: {}", url, ex.getMessage());
        }
        return 0L;
    }

    /**
     * URL에서 마지막 슬래시 제거
     */
    private String trimTrailingSlash(String raw) {
        if (raw == null || raw.isBlank()) {
            return "http://localhost:8080";
        }
        return raw.endsWith("/") ? raw.substring(0, raw.length() - 1) : raw;
    }
}
