package com.ssafy.hebees.monitoring.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.ssafy.hebees.monitoring.client.CadvisorClient;
import com.ssafy.hebees.monitoring.client.CadvisorClient.CadvisorContainerMetrics;
import com.ssafy.hebees.monitoring.client.CadvisorClient.CadvisorSnapshot;
import com.ssafy.hebees.monitoring.config.MonitoringProperties;
import com.ssafy.hebees.monitoring.dto.internal.ServiceTarget;
import com.ssafy.hebees.monitoring.dto.response.CpuUsageResponse;
import com.ssafy.hebees.monitoring.dto.response.MemoryUsageResponse;
import com.ssafy.hebees.monitoring.dto.response.NetworkTrafficResponse;
import com.ssafy.hebees.monitoring.dto.response.ServicePerformanceInfoResponse;
import com.ssafy.hebees.monitoring.dto.response.ServicePerformanceListResponse;
import lombok.extern.slf4j.Slf4j;
import oshi.SystemInfo;
import oshi.hardware.CentralProcessor;
import oshi.hardware.CentralProcessor.TickType;
import oshi.hardware.HardwareAbstractionLayer;
import oshi.hardware.NetworkIF;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.http.codec.ServerSentEvent;
import org.springframework.scheduling.annotation.Async;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Flux;
import reactor.core.scheduler.Schedulers;
import java.time.Duration;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
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
public class MonitoringService {

    private final SystemInfo systemInfo = new SystemInfo();
    private final HardwareAbstractionLayer hal = systemInfo.getHardware();
    private final ObjectMapper objectMapper = new ObjectMapper();
    private final StringRedisTemplate monitoringRedisTemplate;
    private final CadvisorClient cadvisorClient;
    private static final String NETWORK_TRAFFIC_KEY = "monitoring:network:traffic";
    private static final String NETWORK_BYTES_KEY = "monitoring:network:bytes";
    private static final double SQRT_TWO = Math.sqrt(2.0);
    private final double networkBandwidthMbps;
    private final List<ServiceTarget> monitoredServices;
    // 네트워크 대역폭 캐시 (한 번만 감지)
    private volatile Double cachedBandwidthMbps = null;
    private final Object bandwidthLock = new Object();
    // CPU 틱 초기화 플래그
    private volatile boolean cpuTicksInitialized = false;
    private volatile long[] previousCpuTicks = null;
    private final Object cpuTicksLock = new Object();

    public MonitoringService(
        @Qualifier("monitoringRedisTemplate") StringRedisTemplate monitoringRedisTemplate,
        MonitoringProperties monitoringProperties,
        CadvisorClient cadvisorClient
    ) {
        this.monitoringRedisTemplate = monitoringRedisTemplate;
        this.networkBandwidthMbps = monitoringProperties.getNetworkBandwidthMbps();
        this.cadvisorClient = cadvisorClient;
        List<String> serviceTargets = monitoringProperties.getServiceTargets();
        // 빈 리스트이면 모든 컨테이너를 모니터링 (필터링 없음)
        this.monitoredServices = (serviceTargets == null || serviceTargets.isEmpty())
            ? List.of()
            : parseServiceTargets(serviceTargets);
    }

    private static final ZoneId KST = ZoneId.of("Asia/Seoul");
    private static final DateTimeFormatter ISO_FORMATTER = DateTimeFormatter.ofPattern(
        "yyyy-MM-dd'T'HH:mm:ssXXX");

    private String getKstTimestamp() {
        return ZonedDateTime.now(KST).format(ISO_FORMATTER);
    }

    private int calculateActiveCores(int totalCores, double cpuPercent) {
        return (int) Math.round(totalCores * cpuPercent / 100.0);
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

    private long[] cloneTicks(long[] ticks) {
        return ticks == null ? null : Arrays.copyOf(ticks, ticks.length);
    }

    private double calculateCpuUsagePercent(long[] previousTicks, long[] currentTicks) {
        if (previousTicks == null || currentTicks == null
            || previousTicks.length != currentTicks.length) {
            return 0.0;
        }

        long totalDiff = 0;
        long idleDiff = 0;
        int idleIndex = TickType.IDLE.getIndex();
        int iowaitIndex = TickType.IOWAIT.getIndex();

        for (int i = 0; i < currentTicks.length; i++) {
            long diff = currentTicks[i] - previousTicks[i];
            if (diff < 0) {
                diff = 0;
            }

            totalDiff += diff;

            if (i == idleIndex || (i == iowaitIndex && iowaitIndex < currentTicks.length)) {
                idleDiff += diff;
            }
        }

        if (totalDiff <= 0) {
            return 0.0;
        }
        return ((double) (totalDiff - idleDiff) / totalDiff) * 100.0;
    }

    public CpuUsageResponse getCpuData() {
        CentralProcessor processor = hal.getProcessor();

        double cpuPercent;
        try {
            long[] currentTicks = cloneTicks(processor.getSystemCpuLoadTicks());
            synchronized (cpuTicksLock) {
                if (previousCpuTicks != null) {
                    cpuPercent = calculateCpuUsagePercent(previousCpuTicks, currentTicks);
                } else {
                    cpuPercent = 0.0;
                }

                previousCpuTicks = currentTicks;
                cpuTicksInitialized = true;
            }

            if (cpuPercent <= 0.0) {
                double load = processor.getSystemCpuLoad(200);
                if (!Double.isNaN(load) && load > 0.0) {
                    cpuPercent = load * 100.0;
                }
            }
        } catch (Exception e) {
            log.warn("CPU 사용률 측정 중 오류 발생: {}", e.getMessage());
            cpuPercent = 0.0;
        }

        int totalCores = processor.getLogicalProcessorCount();
        int activeCores = calculateActiveCores(totalCores, cpuPercent);

        return new CpuUsageResponse(
            getKstTimestamp(),
            Math.round(cpuPercent * 10.0) / 10.0,
            totalCores,
            activeCores
        );
    }

    public Flux<ServerSentEvent<CpuUsageResponse>> streamCpuUsage() {
        // 첫 번째 호출
        CpuUsageResponse initData = getCpuData();

        return Flux.concat(
                Flux.just(ServerSentEvent.<CpuUsageResponse>builder()
                    .event("init")
                    .data(initData)
                    .build()),
                Flux.interval(Duration.ofSeconds(1))
                    .publishOn(Schedulers.boundedElastic())
                    .map(ignored -> getCpuData())
                    .map(data -> ServerSentEvent.<CpuUsageResponse>builder()
                        .event("update")
                        .data(data)
                        .build())
            ).doOnCancel(() -> log.info("CPU 사용률 스트리밍이 취소되었습니다."))
            .doOnError(error -> log.error("CPU 사용률 스트리밍 중 오류 발생", error));
    }

    public ServicePerformanceListResponse getServicePerformance() {
        CadvisorSnapshot snapshot = cadvisorClient.fetchSnapshot();
        List<CadvisorContainerMetrics> cadvisorContainers = snapshot.containers();
        if (cadvisorContainers.isEmpty()) {
            log.warn(
                "cAdvisor returned no container metrics; responding with an empty service list.");
            return ServicePerformanceListResponse.builder()
                .timestamp(getKstTimestamp())
                .services(List.of())
                .build();
        }

        Map<String, CadvisorContainerMetrics> metricsByCanonical = cadvisorContainers.stream()
            .collect(Collectors.toMap(
                CadvisorContainerMetrics::canonicalName,
                metrics -> metrics,
                (left, right) -> left,
                LinkedHashMap::new
            ));

        Map<String, String> aliasIndex = new LinkedHashMap<>();

        cadvisorContainers.forEach(metrics -> {
            Set<String> aliases = new LinkedHashSet<>(metrics.aliases());
            aliases.add(metrics.canonicalName());
            if (metrics.displayName() != null && !metrics.displayName().isBlank()) {
                aliases.add(metrics.displayName());
            }
            aliases.forEach(alias -> registerAlias(aliasIndex, alias, metrics.canonicalName()));
        });

        TargetSelection selection = resolveTargets(metricsByCanonical, aliasIndex);
        List<ServicePerformanceInfoResponse> services = new ArrayList<>();

        for (String containerKey : selection.orderedContainers()) {
            CadvisorContainerMetrics metrics = metricsByCanonical.get(containerKey);
            boolean running = metrics != null && metrics.running();
            boolean statsAvailable = metrics != null && metrics.metricsAvailable();
            double cpuPercent = statsAvailable ? round(metrics.cpuPercent(), 1) : 0.0;
            double memoryPercent = statsAvailable ? round(metrics.memoryPercent(), 1) : 0.0;
            double compositeScore = running
                ? round(calculateCompositeScore(cpuPercent, memoryPercent), 2)
                : 0.0;
            double loadAvg = metrics != null ? round(metrics.loadAverage(), 2) : 0.0;
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

            services.add(ServicePerformanceInfoResponse.builder()
                .serviceName(serviceName)
                .loadAvg1m(loadAvg)
                .cpuUsagePercent(cpuPercent)
                .memoryUsagePercent(memoryPercent)
                .compositeScore(compositeScore)
                .status(status)
                .build());
        }

        if (!selection.unresolvedTargets().isEmpty()) {
            log.warn("Unresolved monitoring targets from configuration: {}",
                selection.unresolvedTargets());
        }

        return ServicePerformanceListResponse.builder()
            .timestamp(getKstTimestamp())
            .services(services)
            .build();
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

    private String fallbackName(ServiceTarget target) {
        if (target.containerName() != null && !target.containerName().isBlank()) {
            return target.containerName();
        }
        return target.serviceName();
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

    private String normalizeAlias(String value) {
        if (value == null) {
            return "";
        }
        return value.trim().toLowerCase(Locale.ROOT);
    }

    private String collapseAlias(String value) {
        return normalizeAlias(value).replaceAll("[^a-z0-9]", "");
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

    private double calculateCompositeScore(double cpuPercent, double memoryPercent) {
        double rawScore = Math.sqrt(cpuPercent * cpuPercent + memoryPercent * memoryPercent)
            / SQRT_TWO;
        double clamped = Math.max(0.0, Math.min(rawScore, 100.0));
        return clamped;
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

    private double round(double value, int decimals) {
        if (!Double.isFinite(value)) {
            return 0.0;
        }
        double factor = Math.pow(10, decimals);
        return Math.round(value * factor) / factor;
    }

    private double bytesToGb(long bytes) {
        return Math.round((bytes / (1024.0 * 1024.0 * 1024.0)) * 10.0) / 10.0;
    }

    private double calculateMemoryUsagePercent(double usedGb, double totalGb) {
        if (totalGb == 0) {
            return 0.0;
        }
        return Math.round((usedGb / totalGb) * 100.0 * 10.0) / 10.0;
    }

    public MemoryUsageResponse getMemoryData() {
        oshi.hardware.GlobalMemory memory = hal.getMemory();
        double totalMemoryGb = bytesToGb(memory.getTotal());
        double usedMemoryGb = bytesToGb(memory.getTotal() - memory.getAvailable());
        double memoryUsagePercent = calculateMemoryUsagePercent(usedMemoryGb, totalMemoryGb);

        return new MemoryUsageResponse(
            getKstTimestamp(),
            totalMemoryGb,
            usedMemoryGb,
            memoryUsagePercent
        );
    }

    public Flux<ServerSentEvent<MemoryUsageResponse>> streamMemoryUsage() {
        return Flux.concat(
                Flux.just(ServerSentEvent.<MemoryUsageResponse>builder()
                    .event("init")
                    .data(getMemoryData())
                    .build()),
                Flux.interval(Duration.ofSeconds(1))
                    .map(ignored -> getMemoryData())
                    .map(data -> ServerSentEvent.<MemoryUsageResponse>builder()
                        .event("update")
                        .data(data)
                        .build())
            ).doOnCancel(() -> log.info("메모리 사용률 스트리밍이 취소되었습니다."))
            .doOnError(error -> log.error("메모리 사용률 스트리밍 중 오류 발생", error));
    }

    private double bytesToMbps(long bytes, double seconds) {
        if (seconds == 0) {
            return 0.0;
        }
        return Math.round(((bytes * 8.0) / seconds / (1024.0 * 1024.0)) * 10.0) / 10.0;
    }

    private double detectNetworkBandwidth() {
        List<NetworkIF> networkIFs = hal.getNetworkIFs();
        double maxSpeedMbps = 0.0;

        log.debug("네트워크 인터페이스 개수: {}", networkIFs.size());

        for (NetworkIF networkIF : networkIFs) {
            try {
                networkIF.updateAttributes();
                String name = networkIF.getName();
                NetworkIF.IfOperStatus status = networkIF.getIfOperStatus();
                long speed = networkIF.getSpeed();

                log.debug("인터페이스 '{}': 상태={}, 속도={}", name, status, speed);

                boolean isUp =
                    status == NetworkIF.IfOperStatus.UP || status == NetworkIF.IfOperStatus.UNKNOWN;
                boolean hasSpeed = speed > 0;

                // 로컬호스트나 루프백 인터페이스 제외
                boolean isNotLoopback = !name.toLowerCase().contains("lo") &&
                    !name.toLowerCase().contains("loopback") &&
                    !name.toLowerCase().startsWith("veth") &&
                    !name.toLowerCase().startsWith("docker");

                if (isUp && hasSpeed && isNotLoopback) {
                    // OSHI의 getSpeed()는 bps (bits per second)를 반환
                    // bps -> Mbps 변환: 1 Mbps = 1,000,000 bps
                    double speedMbps = speed / 1_000_000.0;

                    // 비현실적으로 큰 값 필터링 (1000 Gbps 이상은 무시)
                    if (speedMbps > 1_000_000) {
                        log.debug("인터페이스 '{}' 속도가 비현실적으로 큼: {} Mbps (원본: {} bps), 무시함", name,
                            speedMbps, speed);
                    } else if (speedMbps > maxSpeedMbps) {
                        maxSpeedMbps = speedMbps;
                        log.debug("인터페이스 '{}' 속도: {} Mbps (원본: {} bps)", name, speedMbps, speed);
                    }
                } else {
                    log.debug("인터페이스 '{}' 필터링됨: isUp={}, hasSpeed={}, isNotLoopback={}",
                        name, isUp, hasSpeed, isNotLoopback);
                }
            } catch (Exception e) {
                log.warn("인터페이스 '{}' 처리 중 오류 발생: {}", networkIF.getName(), e.getMessage());
            }
        }

        if (maxSpeedMbps > 0) {
            log.info("네트워크 대역폭 자동 감지: {} Mbps", maxSpeedMbps);
            return Math.round(maxSpeedMbps * 10.0) / 10.0;
        } else {
            log.warn("네트워크 대역폭 자동 감지 실패: 감지된 인터페이스가 없습니다. 설정값 사용: {} Mbps", networkBandwidthMbps);
            return networkBandwidthMbps;
        }
    }

    private double getNetworkBandwidth() {
        // 캐시된 값이 있으면 재사용
        if (cachedBandwidthMbps != null) {
            return cachedBandwidthMbps;
        }

        // 첫 번째 감지만 수행 (thread-safe)
        synchronized (bandwidthLock) {
            // double-check locking
            if (cachedBandwidthMbps != null) {
                return cachedBandwidthMbps;
            }

            double detectedBandwidth = detectNetworkBandwidth();
            if (detectedBandwidth > 0) {
                cachedBandwidthMbps = detectedBandwidth;
                log.info("네트워크 대역폭 감지 완료 및 캐시: {} Mbps", detectedBandwidth);
                return detectedBandwidth;
            }

            log.info("설정값 사용: {} Mbps", networkBandwidthMbps);
            cachedBandwidthMbps = networkBandwidthMbps;
            return networkBandwidthMbps;
        }
    }

    @Scheduled(fixedRate = 5000) // 5초마다 실행
    @Async
    public void collectNetworkTraffic() {
        try {
            double bandwidthMbps = getNetworkBandwidth();
            List<NetworkIF> networkIFs = hal.getNetworkIFs();
            long totalBytesSent = 0;
            long totalBytesRecv = 0;

            for (NetworkIF networkIF : networkIFs) {
                networkIF.updateAttributes();
                totalBytesSent += networkIF.getBytesSent();
                totalBytesRecv += networkIF.getBytesRecv();
            }

            // 이전 bytes 값 조회
            String previousBytesData = monitoringRedisTemplate.opsForValue().get(NETWORK_BYTES_KEY);
            long previousBytesSent = 0;
            long previousBytesRecv = 0;
            double inboundMbps = 0.0;
            double outboundMbps = 0.0;

            if (previousBytesData != null) {
                try {
                    // 이전 bytes 값 파싱
                    String[] parts = previousBytesData.split(",");
                    if (parts.length == 2) {
                        previousBytesSent = Long.parseLong(parts[0]);
                        previousBytesRecv = Long.parseLong(parts[1]);

                        // 5초 간격으로 변화량 계산
                        long bytesSentDiff = totalBytesSent - previousBytesSent;
                        long bytesRecvDiff = totalBytesRecv - previousBytesRecv;

                        inboundMbps = bytesToMbps(bytesRecvDiff, 5.0);
                        outboundMbps = bytesToMbps(bytesSentDiff, 5.0);
                    }
                } catch (Exception e) {
                    log.warn("이전 네트워크 bytes 데이터 파싱 실패", e);
                }
            }

            // 현재 bytes 값 저장 (다음 계산을 위해)
            String currentBytesData = totalBytesSent + "," + totalBytesRecv;
            monitoringRedisTemplate.opsForValue().set(NETWORK_BYTES_KEY, currentBytesData);

            // 트래픽 데이터 생성 및 Redis에 저장
            NetworkTrafficResponse trafficData = new NetworkTrafficResponse(
                getKstTimestamp(),
                inboundMbps,
                outboundMbps,
                bandwidthMbps
            );

            try {
                String jsonData = objectMapper.writeValueAsString(trafficData);
                monitoringRedisTemplate.opsForValue().set(NETWORK_TRAFFIC_KEY, jsonData);
                log.debug("네트워크 트래픽 데이터 저장 완료: inbound={}, outbound={}", inboundMbps, outboundMbps);
            } catch (JsonProcessingException e) {
                log.error("네트워크 트래픽 데이터 저장 실패", e);
            }
        } catch (Exception e) {
            log.error("네트워크 트래픽 수집 중 오류 발생", e);
        }
    }

    public Flux<ServerSentEvent<NetworkTrafficResponse>> streamNetworkTraffic() {
        double bandwidthMbps = getNetworkBandwidth();

        return Flux.concat(
                Flux.defer(() -> {
                    // Redis에서 초기 데이터 조회
                    String initialData = monitoringRedisTemplate.opsForValue().get(NETWORK_TRAFFIC_KEY);
                    NetworkTrafficResponse data;
                    if (initialData != null) {
                        try {
                            data = objectMapper.readValue(initialData, NetworkTrafficResponse.class);
                        } catch (JsonProcessingException e) {
                            log.warn("초기 네트워크 데이터 파싱 실패", e);
                            data = new NetworkTrafficResponse(
                                getKstTimestamp(),
                                0.0,
                                0.0,
                                bandwidthMbps
                            );
                        }
                    } else {
                        // Redis에 데이터가 없으면 기본값 반환
                        data = new NetworkTrafficResponse(
                            getKstTimestamp(),
                            0.0,
                            0.0,
                            bandwidthMbps
                        );
                    }
                    return Flux.just(ServerSentEvent.<NetworkTrafficResponse>builder()
                        .event("init")
                        .data(data)
                        .build());
                }),
                Flux.interval(Duration.ofSeconds(5))
                    .publishOn(Schedulers.boundedElastic())
                    .map(ignored -> {
                        // Redis에서 최신 데이터 조회
                        String data = monitoringRedisTemplate.opsForValue().get(NETWORK_TRAFFIC_KEY);
                        if (data != null) {
                            try {
                                return objectMapper.readValue(data, NetworkTrafficResponse.class);
                            } catch (JsonProcessingException e) {
                                log.warn("네트워크 데이터 파싱 실패", e);
                            }
                        }
                        // 데이터가 없으면 기본값 반환
                        return new NetworkTrafficResponse(
                            getKstTimestamp(),
                            0.0,
                            0.0,
                            bandwidthMbps
                        );
                    })
                    .map(data -> ServerSentEvent.<NetworkTrafficResponse>builder()
                        .event("update")
                        .data(data)
                        .build())
            ).doOnCancel(() -> log.info("네트워크 트래픽 스트리밍이 취소되었습니다."))
            .doOnError(error -> log.error("네트워크 트래픽 스트리밍 중 오류 발생", error));
    }
}
