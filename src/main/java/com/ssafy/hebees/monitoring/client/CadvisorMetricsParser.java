package com.ssafy.hebees.monitoring.client;

import com.fasterxml.jackson.databind.JsonNode;
import lombok.NoArgsConstructor;
import lombok.extern.slf4j.Slf4j;

import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;

/**
 * cAdvisor 메트릭 파싱 및 계산
 */
@Slf4j
@NoArgsConstructor
public class CadvisorMetricsParser {

    /**
     * JSON 노드를 CadvisorContainerMetrics로 변환
     */
    public static CadvisorContainerMetrics parseMetrics(
        JsonNode node,
        long machineMemoryBytes
    ) {
        String rawName = CadvisorJsonUtils.text(node, "name");
        List<String> aliases = readAliases(node.path("aliases"));
        JsonNode specNode = node.path("spec");
        long specMemoryLimit = readMemoryLimit(specNode.path("memory"));
        Map<String, String> labelMap = readLabels(specNode.path("labels"));

        List<Sample> samples = readSamples(node.path("stats"));
        Set<String> aliasSet = CadvisorNameResolver.buildAliasSet(rawName, aliases, labelMap);
        String canonical = aliasSet.stream().findFirst()
            .orElseGet(() -> CadvisorNameResolver.sanitize(rawName));
        if (canonical == null || canonical.isBlank()) {
            log.debug("Skipping container; no canonical name could be resolved. rawName={}",
                rawName);
            return null;
        }

        double cpuPercent = Double.NaN;
        double memoryPercent = Double.NaN;
        double loadAverage = 0.0;
        JsonNode stateNode = node.path("state");
        JsonNode runningNode = stateNode.path("running");
        boolean running = runningNode.isMissingNode()
            ? !samples.isEmpty()
            : runningNode.asBoolean(!samples.isEmpty());

        Instant startedAt = CadvisorJsonUtils.parseTimestamp(
            CadvisorJsonUtils.text(stateNode, "started_at"));
        if (startedAt == null) {
            startedAt = CadvisorJsonUtils.parseTimestamp(
                CadvisorJsonUtils.text(specNode, "creation_time"));
        }

        if (running) {
            Sample latest = samples.get(samples.size() - 1);
            Sample previous = findPrevious(samples);

            cpuPercent = computeCpuPercent(latest, previous);
            memoryPercent = computeMemoryPercent(latest, specMemoryLimit, machineMemoryBytes);
            loadAverage = Optional.ofNullable(latest.loadAverage()).orElse(0.0);
        }
        if (startedAt == null && !samples.isEmpty()) {
            startedAt = samples.get(0).timestamp();
        }
        Instant lastSeen = samples.isEmpty() ? null : samples.get(samples.size() - 1).timestamp();

        boolean cpuAvailable = !Double.isNaN(cpuPercent);
        boolean memoryAvailable = !Double.isNaN(memoryPercent);
        boolean metricsAvailable = cpuAvailable || memoryAvailable;

        double resolvedCpu = cpuAvailable ? cpuPercent : 0.0;
        double resolvedMemory = memoryAvailable ? memoryPercent : 0.0;

        String displayName = CadvisorNameResolver.resolveDisplayName(canonical, aliasSet, labelMap);

        return new CadvisorContainerMetrics(
            canonical,
            Collections.unmodifiableSet(aliasSet),
            running,
            resolvedCpu,
            resolvedMemory,
            metricsAvailable,
            loadAverage,
            displayName,
            startedAt,
            lastSeen
        );
    }

    /**
     * 이전 샘플 찾기 (CPU 데이터가 있는 것)
     */
    private static Sample findPrevious(List<Sample> samples) {
        for (int idx = samples.size() - 2; idx >= 0; idx--) {
            if (samples.get(idx).cpuTotalNs() != null) {
                return samples.get(idx);
            }
        }
        return null;
    }

    /**
     * CPU 사용률 계산
     */
    private static double computeCpuPercent(Sample latest, Sample previous) {
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

    /**
     * 메모리 사용률 계산
     */
    private static double computeMemoryPercent(Sample latest, long specLimit,
        long machineMemoryBytes) {
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

    /**
     * 샘플 리스트 읽기
     */
    private static List<Sample> readSamples(JsonNode statsNode) {
        if (statsNode == null || !statsNode.isArray()) {
            return List.of();
        }
        List<Sample> samples = new ArrayList<>();
        statsNode.forEach(sampleNode -> {
            Instant timestamp = CadvisorJsonUtils.parseTimestamp(
                CadvisorJsonUtils.text(sampleNode, "timestamp"));
            if (timestamp == null) {
                return;
            }

            JsonNode cpuNode = sampleNode.path("cpu");
            JsonNode cpuUsage = cpuNode.path("usage");
            Long totalNs = CadvisorJsonUtils.number(cpuUsage, "total");
            Double loadAverage = CadvisorJsonUtils.numberDouble(cpuNode, "load_average");

            JsonNode memNode = sampleNode.path("memory");
            Long usageBytes = CadvisorJsonUtils.number(memNode, "usage");
            Long workingSet = CadvisorJsonUtils.number(memNode, "working_set");
            Long limit = CadvisorJsonUtils.number(memNode, "limit");

            samples.add(new Sample(timestamp, totalNs, loadAverage, usageBytes, workingSet, limit));
        });
        return samples;
    }

    /**
     * 라벨 맵 읽기
     */
    private static Map<String, String> readLabels(JsonNode labelsNode) {
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

    /**
     * 메모리 제한 읽기
     */
    private static long readMemoryLimit(JsonNode memoryNode) {
        if (memoryNode == null || memoryNode.isMissingNode()) {
            return 0L;
        }
        Long limit = CadvisorJsonUtils.number(memoryNode, "limit");
        if (limit == null || limit <= 0) {
            limit = CadvisorJsonUtils.number(memoryNode, "limit_in_bytes");
        }
        return limit != null ? limit : 0L;
    }

    /**
     * 별칭 리스트 읽기
     */
    private static List<String> readAliases(JsonNode aliasesNode) {
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

    /**
     * 샘플 데이터 레코드
     */
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

