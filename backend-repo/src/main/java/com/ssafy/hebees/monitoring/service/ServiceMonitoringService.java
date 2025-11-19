package com.ssafy.hebees.monitoring.service;

import com.ssafy.hebees.monitoring.client.CadvisorClient;
import com.ssafy.hebees.monitoring.client.CadvisorContainerMetrics;
import com.ssafy.hebees.monitoring.client.CadvisorSnapshot;
import com.ssafy.hebees.monitoring.config.MonitoringProperties;
import com.ssafy.hebees.monitoring.dto.internal.ServiceTarget;
import com.ssafy.hebees.monitoring.dto.response.ServicePerformanceInfoResponse;
import com.ssafy.hebees.monitoring.dto.response.ServicePerformanceListResponse;
import com.ssafy.hebees.monitoring.dto.response.ServiceStatusInfoResponse;
import com.ssafy.hebees.monitoring.dto.response.ServiceStatusListResponse;
import com.ssafy.hebees.common.util.MonitoringUtils;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import jakarta.annotation.PostConstruct;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class ServiceMonitoringService {

    private final CadvisorClient cadvisorClient;
    private final MonitoringProperties monitoringProperties;
    private List<ServiceTarget> monitoredServices;

    @PostConstruct
    private void init() {
        List<String> serviceTargets = monitoringProperties.getServiceTargets();
        this.monitoredServices = (serviceTargets == null || serviceTargets.isEmpty())
            ? List.of()
            : parseServiceTargets(serviceTargets);
    }

    private List<ServiceTarget> parseServiceTargets(List<String> serviceTargets) {
        if (serviceTargets == null || serviceTargets.isEmpty()) {
            log.info("monitoring.service-targets 설정이 비어 있습니다. 모든 컨테이너를 모니터링합니다.");
            return List.of();
        }
        Map<String, ServiceTarget> mappedTargets = new LinkedHashMap<>();

        serviceTargets.stream()
            .map(String::trim)
            .filter(token -> !token.isEmpty())
            .forEach(token -> {
                String serviceName;
                String containerName;
                int separatorIdx = token.indexOf('=');
                if (separatorIdx >= 0) {
                    serviceName = token.substring(0, separatorIdx).trim();
                    containerName = token.substring(separatorIdx + 1).trim();
                } else {
                    serviceName = token;
                    containerName = token;
                }

                if (serviceName.isEmpty()) {
                    log.warn("service-target '{}'에서 서비스 이름을 추출하지 못했습니다. 항목을 건너뜁니다.", token);
                    return;
                }
                if (containerName.isEmpty()) {
                    containerName = serviceName;
                }

                mappedTargets.put(serviceName, new ServiceTarget(serviceName, containerName));
            });

        if (mappedTargets.isEmpty()) {
            log.info("monitoring.service-targets 파싱 결과가 비어 있습니다. 모든 컨테이너를 모니터링합니다.");
            return List.of();
        }

        log.info("모니터링 대상 서비스 수: {}", mappedTargets.size());
        return List.copyOf(mappedTargets.values());
    }

    private String normalizeAlias(String value) {
        if (value == null) {
            return "";
        }
        return value.trim().toLowerCase(Locale.ROOT);
    }

    private String collapseAlias(String value) {
        return normalizeAlias(value).replaceAll("[^a-z0-9]", "");
    }

    private void registerAlias(Map<String, String> aliasIndex, String alias, String canonical) {
        if (alias == null || alias.isBlank()) {
            return;
        }
        String normalized = normalizeAlias(alias);
        if (!normalized.isEmpty()) {
            aliasIndex.putIfAbsent(normalized, canonical);
        }

        String collapsed = collapseAlias(alias);
        if (!collapsed.isEmpty()) {
            aliasIndex.putIfAbsent(collapsed, canonical);
        }
    }

    private Map<String, String> buildAliasIndex(List<CadvisorContainerMetrics> containers) {
        Map<String, String> aliasIndex = new LinkedHashMap<>();
        containers.forEach(metrics -> {
            Set<String> aliases = new LinkedHashSet<>(metrics.aliases());
            aliases.add(metrics.canonicalName());
            if (metrics.displayName() != null && !metrics.displayName().isBlank()) {
                aliases.add(metrics.displayName());
            }
            aliases.forEach(alias -> registerAlias(aliasIndex, alias, metrics.canonicalName()));
        });
        return aliasIndex;
    }

    private Map<String, CadvisorContainerMetrics> buildMetricsMap(
        List<CadvisorContainerMetrics> containers) {
        return containers.stream()
            .collect(Collectors.toMap(
                CadvisorContainerMetrics::canonicalName,
                metrics -> metrics,
                (left, right) -> left,
                LinkedHashMap::new
            ));
    }

    private String findContainerMatch(ServiceTarget target, Map<String, String> aliasIndex) {
        List<String> candidates = new ArrayList<>();
        if (target.containerName() != null) {
            candidates.add(target.containerName());
        }
        if (target.serviceName() != null) {
            candidates.add(target.serviceName());
        }

        for (String candidate : candidates) {
            String normalized = normalizeAlias(candidate);
            if (!normalized.isEmpty()) {
                String resolved = aliasIndex.get(normalized);
                if (resolved != null) {
                    return resolved;
                }
            }
            String collapsed = collapseAlias(candidate);
            if (!collapsed.isEmpty()) {
                String resolved = aliasIndex.get(collapsed);
                if (resolved != null) {
                    return resolved;
                }
            }
        }

        for (String candidate : candidates) {
            String collapsed = collapseAlias(candidate);
            if (collapsed.length() < 4) {
                continue;
            }
            for (Map.Entry<String, String> entry : aliasIndex.entrySet()) {
                if (entry.getKey().contains(collapsed)) {
                    return entry.getValue();
                }
            }
        }

        return null;
    }

    private String fallbackName(ServiceTarget target) {
        if (target.containerName() != null && !target.containerName().isBlank()) {
            return target.containerName();
        }
        return target.serviceName();
    }

    private static class TargetSelection {

        private final List<String> orderedContainers;
        private final Map<String, String> displayNames;
        private final List<String> unresolvedTargets;

        TargetSelection(
            List<String> orderedContainers,
            Map<String, String> displayNames,
            List<String> unresolvedTargets
        ) {
            this.orderedContainers = orderedContainers;
            this.displayNames = displayNames;
            this.unresolvedTargets = unresolvedTargets;
        }

        List<String> orderedContainers() {
            return orderedContainers;
        }

        Optional<String> serviceNameFor(String key) {
            return Optional.ofNullable(displayNames.get(key));
        }

        List<String> unresolvedTargets() {
            return unresolvedTargets;
        }
    }

    private TargetSelection resolveTargets(
        Map<String, CadvisorContainerMetrics> metricsByCanonical,
        Map<String, String> aliasIndex
    ) {
        List<String> ordered = new ArrayList<>();
        Map<String, String> displayNames = new LinkedHashMap<>();
        List<String> unresolved = new ArrayList<>();
        Set<String> seen = new LinkedHashSet<>();

        if (monitoredServices.isEmpty()) {
            ordered.addAll(metricsByCanonical.keySet());
            seen.addAll(metricsByCanonical.keySet());
        } else {
            for (ServiceTarget target : monitoredServices) {
                String matched = findContainerMatch(target, aliasIndex);
                if (matched != null) {
                    if (seen.add(matched)) {
                        ordered.add(matched);
                    }
                    displayNames.putIfAbsent(matched, target.serviceName());
                } else {
                    String fallback = fallbackName(target);
                    if (fallback != null && !fallback.isBlank() && seen.add(fallback)) {
                        ordered.add(fallback);
                        displayNames.put(fallback, target.serviceName());
                    }
                    unresolved.add(target.containerName());
                }
            }
            if (ordered.isEmpty()) {
                log.warn("monitoring.service-targets 설정과 일치하는 컨테이너를 찾지 못했습니다. 구성 값을 확인해주세요.");
            }
        }

        return new TargetSelection(ordered, displayNames, unresolved);
    }

    private double calculateCompositeScore(double cpuPercent, double memoryPercent) {
        double rawScore =
            Math.sqrt(cpuPercent * cpuPercent + memoryPercent * memoryPercent)
                / MonitoringUtils.SQRT_TWO;
        return Math.max(0.0, Math.min(rawScore, 100.0));
    }

    private String determineStatus(double compositeScore) {
        if (compositeScore < 70.0) {
            return "NORMAL";
        }
        if (compositeScore <= 90.0) {
            return "WARNING";
        }
        return "CRITICAL";
    }

    public ServicePerformanceListResponse getServicePerformance() {
        CadvisorSnapshot snapshot = cadvisorClient.fetchSnapshot();
        List<CadvisorContainerMetrics> cadvisorContainers = snapshot.containers();
        if (cadvisorContainers.isEmpty()) {
            log.warn(
                "cAdvisor returned no container metrics; responding with an empty service list.");
            return new ServicePerformanceListResponse(MonitoringUtils.getKstTimestamp(), List.of());
        }

        Map<String, CadvisorContainerMetrics> metricsByCanonical = buildMetricsMap(
            cadvisorContainers);
        Map<String, String> aliasIndex = buildAliasIndex(cadvisorContainers);
        TargetSelection selection = resolveTargets(metricsByCanonical, aliasIndex);
        List<ServicePerformanceInfoResponse> services = new ArrayList<>();

        for (String containerKey : selection.orderedContainers()) {
            CadvisorContainerMetrics metrics = metricsByCanonical.get(containerKey);
            boolean running = metrics != null && metrics.running();
            boolean statsAvailable = metrics != null && metrics.metricsAvailable();
            double cpuPercent =
                statsAvailable ? MonitoringUtils.round(metrics.cpuPercent(), 1) : 0.0;
            double memoryPercent =
                statsAvailable ? MonitoringUtils.round(metrics.memoryPercent(), 1) : 0.0;
            double compositeScore = running
                ? MonitoringUtils.round(calculateCompositeScore(cpuPercent, memoryPercent), 2)
                : 0.0;
            String status = running ? determineStatus(compositeScore) : "EXITED";
            String serviceName = selection.serviceNameFor(containerKey)
                .orElseGet(() -> {
                    if (metrics == null) {
                        return containerKey;
                    }
                    if (metrics.displayName() != null && !metrics.displayName().isBlank()) {
                        return metrics.displayName();
                    }
                    return metrics.canonicalName();
                });

            services.add(new ServicePerformanceInfoResponse(
                serviceName,
                cpuPercent,
                memoryPercent,
                compositeScore,
                status
            ));
        }

        if (!selection.unresolvedTargets().isEmpty()) {
            log.warn("Unresolved monitoring targets from configuration: {}",
                selection.unresolvedTargets());
        }

        return new ServicePerformanceListResponse(MonitoringUtils.getKstTimestamp(), services);
    }

    private ServiceStatusInfoResponse buildServiceStatus(
        ServiceTarget target,
        CadvisorContainerMetrics metrics
    ) {
        ServiceStatusInfoResponse.Status status;
        String startedAt = null;
        String uptimeSeconds = null;

        if (metrics == null) {
            status = ServiceStatusInfoResponse.Status.UNKNOWN;
        } else if (metrics.running()) {
            status = ServiceStatusInfoResponse.Status.RUNNING;
            Instant startedInstant = metrics.startedAt();
            if (startedInstant != null) {
                startedAt = MonitoringUtils.formatInstant(startedInstant);
                Long uptimeSecondsValue = calculateUptimeSeconds(startedInstant);
                uptimeSeconds = formatUptime(uptimeSecondsValue);
            }
        } else {
            status = ServiceStatusInfoResponse.Status.STOPPED;
        }

        return new ServiceStatusInfoResponse(
            target.serviceName(),
            status.name(),
            startedAt,
            uptimeSeconds
        );
    }

    public ServiceStatusListResponse getServiceStatus() {
        CadvisorSnapshot snapshot = cadvisorClient.fetchSnapshot();
        List<CadvisorContainerMetrics> cadvisorContainers = snapshot.containers();
        Map<String, CadvisorContainerMetrics> metricsByCanonical = buildMetricsMap(
            cadvisorContainers);
        Map<String, String> aliasIndex = buildAliasIndex(cadvisorContainers);

        List<ServiceStatusInfoResponse> services = new ArrayList<>();
        if (monitoredServices.isEmpty()) {
            log.warn("monitoring.service-targets 설정이 비어 있어 서비스 상태를 조회할 대상이 없습니다.");
        } else {
            for (ServiceTarget target : monitoredServices) {
                String matched = findContainerMatch(target, aliasIndex);
                CadvisorContainerMetrics metrics = matched != null
                    ? metricsByCanonical.get(matched)
                    : null;
                services.add(buildServiceStatus(target, metrics));
            }
        }

        return new ServiceStatusListResponse(MonitoringUtils.getKstTimestamp(), services);
    }

    private Long calculateUptimeSeconds(Instant startedAt) {
        if (startedAt == null) {
            return null;
        }
        long seconds = Duration.between(startedAt, Instant.now()).getSeconds();
        return Math.max(seconds, 0);
    }

    private String formatUptime(Long seconds) {
        if (seconds == null) {
            return null;
        }
        if (seconds <= 0) {
            return "0s";
        }
        long remaining = seconds;
        long days = remaining / MonitoringUtils.SECONDS_PER_DAY;
        remaining %= MonitoringUtils.SECONDS_PER_DAY;
        long hours = remaining / MonitoringUtils.SECONDS_PER_HOUR;
        remaining %= MonitoringUtils.SECONDS_PER_HOUR;
        long minutes = remaining / MonitoringUtils.SECONDS_PER_MINUTE;
        long secs = remaining % MonitoringUtils.SECONDS_PER_MINUTE;

        List<String> parts = new ArrayList<>();
        if (days > 0) {
            parts.add(days + "d");
        }
        if (hours > 0) {
            parts.add(hours + "h");
        }
        if (minutes > 0 && parts.size() < 3) {
            parts.add(minutes + "m");
        }
        if (secs > 0 && parts.isEmpty()) {
            parts.add(secs + "s");
        }
        if (parts.isEmpty()) {
            parts.add("0s");
        }
        return String.join(" ", parts);
    }
}

