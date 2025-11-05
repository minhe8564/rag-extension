package com.ssafy.hebees.monitoring.client;

import com.fasterxml.jackson.databind.JsonNode;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

import java.time.Duration;
import java.time.Instant;
import java.time.OffsetDateTime;
import java.time.format.DateTimeParseException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.Locale;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;

@Slf4j
@Component
public class CadvisorClient {

    private final RestTemplate restTemplate;
    private final String cadvisorBaseUrl;

    private static final String[] PREFERRED_LABEL_KEYS = new String[]{
        "io.kubernetes.container.name",
        "io.kubernetes.pod.name",
        "io.kubernetes.deployment.name",
        "io.kubernetes.statefulset.name",
        "io.openshift.serviceName",
        "com.docker.compose.service",
        "io.docker.compose.service",
        "container_label_com_docker_compose_service",
        "container_label_com_docker_swarm_service_name",
        "container_label_io_kubernetes_container_name",
        "container_label_io_kubernetes_pod_name",
        "name"
    };

    public CadvisorClient(
        RestTemplate restTemplate,
        @Value("${monitoring.cadvisor.base-url:http://localhost:8080}") String cadvisorBaseUrl
    ) {
        this.restTemplate = restTemplate;
        this.cadvisorBaseUrl = trimTrailingSlash(cadvisorBaseUrl);
    }

    public CadvisorSnapshot fetchSnapshot() {
        JsonNode containerRoot = fetchContainersNode();
        long machineMemoryBytes = fetchMachineMemoryBytes();

        if (containerRoot == null || containerRoot.isMissingNode()) {
            log.warn("cAdvisor returned no container payload.");
            return CadvisorSnapshot.empty(machineMemoryBytes);
        }

        List<CadvisorContainerMetrics> containers = new ArrayList<>();
        containerRoot.fields().forEachRemaining(entry -> {
            CadvisorContainerMetrics metrics = toMetrics(entry.getValue(), machineMemoryBytes);
            if (metrics != null) {
                containers.add(metrics);
            }
        });

        return new CadvisorSnapshot(Collections.unmodifiableList(containers), machineMemoryBytes);
    }

    private JsonNode fetchContainersNode() {
        String url = cadvisorBaseUrl + "/api/v1.3/docker";
        try {
            ResponseEntity<JsonNode> response = restTemplate.getForEntity(url, JsonNode.class);
            return response.getStatusCode().is2xxSuccessful() ? response.getBody() : null;
        } catch (RestClientException ex) {
            log.warn("Failed to call cAdvisor at {}: {}", url, ex.getMessage());
            return null;
        }
    }

    private long fetchMachineMemoryBytes() {
        String url = cadvisorBaseUrl + "/api/v1.3/machine";
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

    private CadvisorContainerMetrics toMetrics(JsonNode node, long machineMemoryBytes) {
        String rawName = text(node, "name");
        List<String> aliases = readAliases(node.path("aliases"));
        JsonNode specNode = node.path("spec");
        long specMemoryLimit = readMemoryLimit(specNode.path("memory"));
        Map<String, String> labelMap = readLabels(specNode.path("labels"));

        List<Sample> samples = readSamples(node.path("stats"));
        Set<String> aliasSet = buildAliasSet(rawName, aliases, labelMap);
        String canonical = aliasSet.stream().findFirst().orElseGet(() -> sanitize(rawName));
        if (canonical == null || canonical.isBlank()) {
            log.debug("Skipping container; no canonical name could be resolved. rawName={}",
                rawName);
            return null;
        }

        double cpuPercent = Double.NaN;
        double memoryPercent = Double.NaN;
        double loadAverage = 0.0;
        boolean running = !samples.isEmpty();

        if (running) {
            Sample latest = samples.get(samples.size() - 1);
            Sample previous = findPrevious(samples);

            cpuPercent = computeCpuPercent(latest, previous);
            memoryPercent = computeMemoryPercent(latest, specMemoryLimit, machineMemoryBytes);
            loadAverage = Optional.ofNullable(latest.loadAverage()).orElse(0.0);
        }

        boolean cpuAvailable = !Double.isNaN(cpuPercent);
        boolean memoryAvailable = !Double.isNaN(memoryPercent);
        boolean metricsAvailable = cpuAvailable || memoryAvailable;

        double resolvedCpu = cpuAvailable ? cpuPercent : 0.0;
        double resolvedMemory = memoryAvailable ? memoryPercent : 0.0;

        String displayName = resolveDisplayName(canonical, aliasSet, labelMap);

        return new CadvisorContainerMetrics(
            canonical,
            Collections.unmodifiableSet(aliasSet),
            running,
            resolvedCpu,
            resolvedMemory,
            metricsAvailable,
            loadAverage,
            displayName
        );
    }

    private Sample findPrevious(List<Sample> samples) {
        for (int idx = samples.size() - 2; idx >= 0; idx--) {
            if (samples.get(idx).cpuTotalNs() != null) {
                return samples.get(idx);
            }
        }
        return null;
    }

    private double computeCpuPercent(Sample latest, Sample previous) {
        if (latest == null || previous == null) {
            return Double.NaN;
        }
        Long latestUsage = latest.cpuTotalNs();
        Long prevUsage = previous.cpuTotalNs();
        if (latestUsage == null || prevUsage == null || latestUsage <= prevUsage) {
            return Double.NaN;
        }
        long usageDiff = latestUsage - prevUsage;
        Duration duration = Duration.between(previous.timestamp(), latest.timestamp());
        long nanos = duration.toNanos();
        if (nanos <= 0) {
            return Double.NaN;
        }
        double usageRatio = (double) usageDiff / nanos;
        return usageRatio * 100.0;
    }

    private double computeMemoryPercent(Sample latest, long specLimit, long machineMemoryBytes) {
        if (latest == null) {
            return Double.NaN;
        }
        Long workingSet = latest.memoryWorkingSetBytes();
        Long usage = latest.memoryUsageBytes();
        Long statsLimit = latest.memoryLimitBytes();
        long limit = Optional.ofNullable(statsLimit)
            .filter(val -> val > 0)
            .orElseGet(() -> specLimit > 0 ? specLimit : machineMemoryBytes);
        long used = Optional.ofNullable(workingSet).filter(val -> val > 0)
            .orElse(usage != null ? usage : 0L);

        if (limit <= 0 || used <= 0) {
            return Double.NaN;
        }
        double percent = (double) used / limit * 100.0;
        return Math.max(0.0, Math.min(percent, 100.0));
    }

    private List<Sample> readSamples(JsonNode statsNode) {
        if (statsNode == null || !statsNode.isArray()) {
            return List.of();
        }
        List<Sample> samples = new ArrayList<>();
        statsNode.forEach(sampleNode -> {
            Instant timestamp = parseTimestamp(text(sampleNode, "timestamp"));
            if (timestamp == null) {
                return;
            }

            JsonNode cpuNode = sampleNode.path("cpu");
            JsonNode cpuUsage = cpuNode.path("usage");
            Long totalNs = number(cpuUsage, "total");
            Double loadAverage = numberDouble(cpuNode, "load_average");

            JsonNode memNode = sampleNode.path("memory");
            Long usageBytes = number(memNode, "usage");
            Long workingSet = number(memNode, "working_set");
            Long limit = number(memNode, "limit");

            samples.add(new Sample(timestamp, totalNs, loadAverage, usageBytes, workingSet, limit));
        });
        return samples;
    }

    private Map<String, String> readLabels(JsonNode labelsNode) {
        if (labelsNode == null || !labelsNode.isObject()) {
            return Map.of();
        }
        Map<String, String> result = new LinkedHashMap<>();
        labelsNode.fields().forEachRemaining(entry -> {
            if (entry.getValue().isTextual()) {
                result.put(entry.getKey(), entry.getValue().asText());
            }
        });
        return result;
    }

    private long readMemoryLimit(JsonNode memoryNode) {
        if (memoryNode == null || memoryNode.isMissingNode()) {
            return 0L;
        }
        Long limit = number(memoryNode, "limit");
        if (limit == null || limit <= 0) {
            limit = number(memoryNode, "limit_in_bytes");
        }
        return limit != null ? limit : 0L;
    }


    private String resolveDisplayName(String canonical, Set<String> aliases,
        Map<String, String> labels) {
        for (String key : PREFERRED_LABEL_KEYS) {
            String candidate = labels.get(key);
            candidate = sanitize(candidate);
            if (isUsableDisplayName(candidate)) {
                return candidate;
            }
        }

        for (String alias : aliases) {
            String candidate = sanitize(alias);
            if (isUsableDisplayName(candidate)) {
                return candidate;
            }
        }

        String cleanedCanonical = sanitize(canonical);
        if (isUsableDisplayName(cleanedCanonical)) {
            return cleanedCanonical;
        }
        if (cleanedCanonical != null && !cleanedCanonical.isBlank()) {
            return cleanedCanonical;
        }
        return canonical;
    }

    private boolean isUsableDisplayName(String value) {
        if (value == null || value.isBlank()) {
            return false;
        }
        String lower = value.toLowerCase(Locale.ROOT);
        if (lower.startsWith("system.slice")) {
            return false;
        }
        if (lower.startsWith("kubepods")) {
            return false;
        }
        if (lower.startsWith("docker-")) {
            return false;
        }
        if (lower.startsWith("libpod-")) {
            return false;
        }
        if (lower.matches("[0-9a-f]{12,}")) {
            return false;
        }
        return true;
    }

    private List<String> readAliases(JsonNode aliasesNode) {
        if (aliasesNode == null || !aliasesNode.isArray()) {
            return List.of();
        }
        List<String> aliases = new ArrayList<>();
        aliasesNode.forEach(alias -> {
            if (alias.isTextual()) {
                aliases.add(alias.asText());
            }
        });
        return aliases;
    }

    private Set<String> buildAliasSet(String rawName, List<String> aliases,
        Map<String, String> labels) {
        LinkedHashSet<String> values = new LinkedHashSet<>();
        addVariants(values, rawName);
        aliases.forEach(alias -> addVariants(values, alias));
        labels.values().forEach(value -> addVariants(values, value));
        values.removeIf(str -> str == null || str.isBlank());
        return values;
    }

    private void addVariants(Set<String> values, String raw) {
        String cleaned = sanitize(raw);
        if (cleaned == null || cleaned.isBlank()) {
            return;
        }
        values.add(cleaned);
        String withoutDashIndex = cleaned.replaceAll("[-_][0-9]+$", "");
        if (!withoutDashIndex.isBlank()) {
            values.add(withoutDashIndex);
        }
    }

    private Instant parseTimestamp(String raw) {
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

    private String text(JsonNode node, String field) {
        JsonNode value = node == null ? null : node.get(field);
        return value != null && value.isTextual() ? value.asText() : null;
    }

    private Long number(JsonNode node, String field) {
        JsonNode value = node == null ? null : node.get(field);
        return value != null && value.isNumber() ? value.longValue() : null;
    }

    private Double numberDouble(JsonNode node, String field) {
        JsonNode value = node == null ? null : node.get(field);
        return value != null && value.isNumber() ? value.doubleValue() : null;
    }

    private String sanitize(String raw) {
        if (raw == null) {
            return null;
        }
        String cleaned = raw.trim();
        while (cleaned.startsWith("/")) {
            cleaned = cleaned.substring(1);
        }
        cleaned = cleaned.replace("docker://", "")
            .replace("containerd://", "");
        if (cleaned.startsWith("docker/")) {
            cleaned = cleaned.substring("docker/".length());
        }
        if (cleaned.startsWith("system.slice/")) {
            cleaned = cleaned.substring("system.slice/".length());
        }
        if (cleaned.endsWith(".scope")) {
            cleaned = cleaned.substring(0, cleaned.length() - ".scope".length());
        }
        if (cleaned.startsWith("docker-") && cleaned.length() > "docker-".length()) {
            String remainder = cleaned.substring("docker-".length());
            if (remainder.matches("[0-9a-f]{8,}")) {
                cleaned = remainder;
            }
        }
        if (cleaned.startsWith("libpod-") && cleaned.length() > "libpod-".length()) {
            String remainder = cleaned.substring("libpod-".length());
            if (remainder.matches("[0-9a-f]{8,}")) {
                cleaned = remainder;
            }
        }
        if (cleaned.startsWith("containerd-") && cleaned.length() > "containerd-".length()) {
            String remainder = cleaned.substring("containerd-".length());
            if (remainder.matches("[0-9a-f]{8,}")) {
                cleaned = remainder;
            }
        }
        return cleaned;
    }

    private String trimTrailingSlash(String raw) {
        if (raw == null || raw.isBlank()) {
            return "http://localhost:8080";
        }
        return raw.endsWith("/") ? raw.substring(0, raw.length() - 1) : raw;
    }

    public record CadvisorSnapshot(
        List<CadvisorContainerMetrics> containers,
        long machineMemoryBytes
    ) {

        public static CadvisorSnapshot empty(long memoryBytes) {
            return new CadvisorSnapshot(List.of(), memoryBytes);
        }
    }

    public record CadvisorContainerMetrics(
        String canonicalName,
        Set<String> aliases,
        boolean running,
        double cpuPercent,
        double memoryPercent,
        boolean metricsAvailable,
        double loadAverage,
        String displayName
    ) {

    }

    private record Sample(
        Instant timestamp,
        Long cpuTotalNs,
        Double loadAverage,
        Long memoryUsageBytes,
        Long memoryWorkingSetBytes,
        Long memoryLimitBytes
    ) {

    }
}
