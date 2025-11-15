package com.ssafy.hebees.monitoring.client;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.ssafy.hebees.chat.config.RunpodProperties;
import com.ssafy.hebees.common.exception.BusinessException;
import com.ssafy.hebees.common.exception.ErrorCode;
import com.ssafy.hebees.common.util.MonitoringUtils;
import com.ssafy.hebees.monitoring.dto.response.RunpodCpuUsageResponse;
import com.ssafy.hebees.monitoring.dto.response.RunpodGpuUsageResponse;
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

import java.util.HashMap;
import java.util.Map;

/**
 * Runpod 공식 API를 사용하여 GPU/CPU 사용량을 조회하는 클라이언트
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class RunpodMonitoringClient {

    private final RestTemplate restTemplate;
    private final RunpodProperties properties;
    private final ObjectMapper objectMapper;

    /**
     * Runpod Pod의 GPU 사용량 조회
     *
     * @param podId Pod ID
     * @return GPU 사용량 정보
     */
    public RunpodGpuUsageResponse getGpuUsage(String podId) {
        if (!StringUtils.hasText(properties.getApiKey())) {
            log.error("Runpod API key is not configured");
            throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
        }

        try {
            String query = buildGpuQuery(podId);
            JsonNode response = executeGraphQLQuery(query);
            return parseGpuResponse(response);
        } catch (Exception e) {
            log.error("Failed to get GPU usage from Runpod API", e);
            throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
        }
    }

    /**
     * Runpod Pod의 CPU 사용량 조회
     *
     * @param podId Pod ID
     * @return CPU 사용량 정보
     */
    public RunpodCpuUsageResponse getCpuUsage(String podId) {
        if (!StringUtils.hasText(properties.getApiKey())) {
            log.error("Runpod API key is not configured");
            throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
        }

        try {
            String query = buildCpuQuery(podId);
            JsonNode response = executeGraphQLQuery(query);
            return parseCpuResponse(response);
        } catch (Exception e) {
            log.error("Failed to get CPU usage from Runpod API", e);
            throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
        }
    }

    /**
     * GraphQL 쿼리 실행
     */
    private JsonNode executeGraphQLQuery(String query) throws JsonProcessingException {
        String url = StringUtils.hasText(properties.getApiBaseUrl())
            ? properties.getApiBaseUrl()
            : "https://api.runpod.io/graphql";

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        headers.setBearerAuth(properties.getApiKey());

        Map<String, String> requestBody = new HashMap<>();
        requestBody.put("query", query);

        HttpEntity<Map<String, String>> entity = new HttpEntity<>(requestBody, headers);

        try {
            ResponseEntity<String> response = restTemplate.postForEntity(url, entity, String.class);
            if (!response.getStatusCode().is2xxSuccessful() || response.getBody() == null) {
                log.error("Runpod API request failed: status={}, body={}",
                    response.getStatusCode(), response.getBody());
                throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
            }

            JsonNode root = objectMapper.readTree(response.getBody());
            if (root.has("errors")) {
                log.error("Runpod API GraphQL errors: {}", root.get("errors"));
                throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
            }

            return root.get("data");
        } catch (RestClientException | JsonProcessingException e) {
            log.error("Failed to call Runpod API", e);
            throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
        }
    }

    /**
     * GPU 조회용 GraphQL 쿼리 생성 명세서에 맞게 수정
     */
    private String buildGpuQuery(String podId) {
        // podId 검증 및 이스케이프 처리
        if (!StringUtils.hasText(podId)) {
            throw new BusinessException(ErrorCode.INVALID_INPUT);
        }
        // GraphQL 문자열 값 이스케이프 (따옴표, 줄바꿈 등)
        String escapedPodId = podId.replace("\"", "\\\"").replace("\n", "\\n").replace("\r", "\\r");
        return String.format("""
            query {
              pod(input: {podId: "%s"}) {
                id
                name
                runtime {
                  gpus {
                    id
                    gpuUtilPercent
                    memoryUtilPercent
                  }
                }
                machine {
                  gpuDisplayName
                  gpuType {
                    memoryInGb
                  }
                }
              }
            }
            """, escapedPodId);
    }

    /**
     * CPU 조회용 GraphQL 쿼리 생성 명세서에 맞게 수정
     */
    private String buildCpuQuery(String podId) {
        return String.format("""
            query {
              pod(input: {podId: "%s"}) {
                id
                name
                runtime {
                  container {
                    cpuPercent
                    memoryPercent
                  }
                }
                machine {
                  cpuCount
                }
              }
            }
            """, podId);
    }

    /**
     * GPU 응답 파싱 명세서에 맞게 수정
     */
    private RunpodGpuUsageResponse parseGpuResponse(JsonNode data) {
        JsonNode pod = data.path("pod");
        if (pod.isMissingNode() || pod.isNull()) {
            throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
        }

        JsonNode runtime = pod.path("runtime");
        JsonNode machine = pod.path("machine");

        // GPU 정보는 runtime.gpus 배열에서 가져옴
        JsonNode gpus = runtime.path("gpus");
        if (gpus.isMissingNode() || !gpus.isArray() || gpus.size() == 0) {
            throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
        }

        // 첫 번째 GPU 사용
        JsonNode gpu = gpus.get(0);
        int gpuIndex = 0;
        double gpuUtilPercent = gpu.path("gpuUtilPercent").asDouble(0.0);
        double memoryUtilPercent = gpu.path("memoryUtilPercent").asDouble(0.0);

        // GPU 이름과 메모리는 machine에서 가져옴
        String gpuName = machine.path("gpuDisplayName").asText("Unknown GPU");
        JsonNode gpuType = machine.path("gpuType");
        long memoryTotalGb = gpuType.path("memoryInGb").asLong(0);
        long memoryTotalMB = memoryTotalGb * 1024;

        // 사용된 메모리는 memoryUtilPercent로 계산
        long memoryUsedMB = (long) (memoryTotalMB * memoryUtilPercent / 100.0);

        // Runpod API는 GPU 온도 정보를 직접 제공하지 않음
        int temperatureCelsius = 0;

        return new RunpodGpuUsageResponse(
            MonitoringUtils.getKstTimestamp(),
            gpuIndex,
            gpuName,
            MonitoringUtils.round(gpuUtilPercent, 1),
            MonitoringUtils.round(memoryUtilPercent, 1),
            memoryUsedMB,
            memoryTotalMB,
            temperatureCelsius
        );
    }

    /**
     * CPU 응답 파싱 명세서에 맞게 수정
     */
    private RunpodCpuUsageResponse parseCpuResponse(JsonNode data) {
        JsonNode pod = data.path("pod");
        if (pod.isMissingNode() || pod.isNull()) {
            throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
        }

        JsonNode runtime = pod.path("runtime");
        if (runtime.isMissingNode() || runtime.isNull()) {
            throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
        }

        JsonNode container = runtime.path("container");
        JsonNode machine = pod.path("machine");

        // CPU 사용률은 container.cpuPercent에서 가져옴
        double cpuUtilPercent = container.path("cpuPercent").asDouble(0.0);
        int totalCores = machine.path("cpuCount").asInt(0);
        int activeCores = (int) Math.round(totalCores * cpuUtilPercent / 100.0);

        // Load average는 명세서에 없으므로 0으로 설정
        // 또는 latestTelemetry에서 가져올 수 있지만, 여기서는 0으로 설정
        double loadAverage1m = 0.0;
        double loadAverage5m = 0.0;
        double loadAverage15m = 0.0;

        return new RunpodCpuUsageResponse(
            MonitoringUtils.getKstTimestamp(),
            MonitoringUtils.round(cpuUtilPercent, 1),
            totalCores,
            activeCores,
            MonitoringUtils.round(loadAverage1m, 2),
            MonitoringUtils.round(loadAverage5m, 2),
            MonitoringUtils.round(loadAverage15m, 2)
        );
    }
}
