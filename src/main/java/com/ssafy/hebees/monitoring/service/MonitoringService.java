package com.ssafy.hebees.monitoring.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.ssafy.hebees.monitoring.dto.internal.CpuMemUsage;
import com.ssafy.hebees.monitoring.dto.internal.DockerContainerStatus;
import com.ssafy.hebees.monitoring.dto.internal.ServiceTarget;
import com.ssafy.hebees.monitoring.dto.response.CpuUsageResponse;
import com.ssafy.hebees.monitoring.dto.response.MemoryUsageResponse;
import com.ssafy.hebees.monitoring.dto.response.NetworkTrafficResponse;
import com.ssafy.hebees.monitoring.dto.response.ServicePerformanceInfoResponse;
import com.ssafy.hebees.monitoring.dto.response.ServicePerformanceListResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import oshi.SystemInfo;
import oshi.hardware.CentralProcessor;
import oshi.hardware.CentralProcessor.TickType;
import oshi.hardware.HardwareAbstractionLayer;
import oshi.hardware.NetworkIF;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.scheduling.annotation.Async;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.http.codec.ServerSentEvent;
import reactor.core.publisher.Flux;
import reactor.core.scheduler.Schedulers;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.TimeUnit;

@Slf4j
@Service
public class MonitoringService {

    private final SystemInfo systemInfo = new SystemInfo();
    private final HardwareAbstractionLayer hal = systemInfo.getHardware();
    private final ObjectMapper objectMapper = new ObjectMapper();
    private final StringRedisTemplate monitoringRedisTemplate;

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
        @Value("${monitoring.network-bandwidth-mbps:1000.0}") double networkBandwidthMbps,
        @Value("${monitoring.service-targets:}") List<String> serviceTargets
    ) {
        this.monitoringRedisTemplate = monitoringRedisTemplate;
        this.networkBandwidthMbps = networkBandwidthMbps;
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

        return CpuUsageResponse.builder()
            .timestamp(getKstTimestamp())
            .cpuUsagePercent(Math.round(cpuPercent * 10.0) / 10.0)
            .totalCores(totalCores)
            .activeCores(activeCores)
            .build();
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
        // docker ps -a로 모든 컨테이너 조회
        Map<String, DockerContainerStatus> containerStatusMap = getAllContainers();

        // 디버깅: 발견된 컨테이너 목록 로깅
        log.info("발견된 컨테이너 수: {}", containerStatusMap.size());
        containerStatusMap.forEach((name, status) ->
            log.debug("컨테이너: {} - 상태: {} - 실행중: {}", name, status.rawStatus(), status.running())
        );

        // 모니터링 대상 서비스 결정
        List<String> targetContainerNames = new ArrayList<>();

        if (monitoredServices.isEmpty()) {
            // service-targets가 비어있으면 모든 컨테이너 모니터링
            log.info("모니터링 대상 서비스가 지정되지 않았습니다. 모든 컨테이너를 모니터링합니다.");
            targetContainerNames.addAll(containerStatusMap.keySet());
        } else {
            // service-targets에 지정된 서비스만 모니터링
            log.info("모니터링 대상 서비스 수: {}", monitoredServices.size());

            // 각 서비스에 대해 실제 컨테이너 이름 매칭
            for (ServiceTarget target : monitoredServices) {
                String serviceName = target.serviceName();
                String containerName = target.containerName();

                // 정확한 이름 매칭 시도
                DockerContainerStatus dockerStatus = containerStatusMap.get(containerName);

                // 정확한 매칭 실패 시, 부분 매칭 시도
                if (dockerStatus == null) {
                    String finalContainerName = containerName;
                    String finalServiceName = serviceName;
                    String matchedName = containerStatusMap.keySet().stream()
                        .filter(name -> {
                            // 컨테이너 이름에 서비스 이름이 포함되어 있는지 확인 (단, 너무 짧은 매칭은 제외)
                            return name.equals(finalContainerName) ||
                                (name.contains(finalContainerName)
                                    && finalContainerName.length() >= 5) ||
                                (name.contains(finalServiceName) && finalServiceName.length() >= 5);
                        })
                        .findFirst()
                        .orElse(null);

                    if (matchedName != null) {
                        log.info("컨테이너 '{}'를 부분 매칭으로 찾았습니다: '{}'", containerName, matchedName);
                        targetContainerNames.add(matchedName);
                    } else {
                        log.warn("컨테이너 '{}'를 찾지 못했습니다. 발견된 컨테이너: {}",
                            containerName, containerStatusMap.keySet());
                        // 매칭 실패해도 원래 이름으로 추가 (NOT_FOUND 상태로 표시)
                        targetContainerNames.add(containerName);
                    }
                } else {
                    targetContainerNames.add(containerName);
                }
            }
        }

        log.info("모니터링 대상 컨테이너 수: {}", targetContainerNames.size());
        targetContainerNames.forEach(name -> log.debug("모니터링 대상 컨테이너: {}", name));

        // 실행 중인 컨테이너만 통계 수집 대상에 추가
        List<String> runningContainers = targetContainerNames.stream()
            .filter(containerName -> {
                DockerContainerStatus status = containerStatusMap.get(containerName);
                return status != null && status.running();
            })
            .distinct()
            .toList();

        log.info("실행 중인 컨테이너 수: {}", runningContainers.size());
        runningContainers.forEach(name -> log.debug("실행 중인 컨테이너: {}", name));

        // 실행 중인 컨테이너로 통계 수집
        Map<String, CpuMemUsage> usageMap = fetchCpuMemStats(runningContainers);
        List<ServicePerformanceInfoResponse> services = new ArrayList<>();

        // 모니터링 대상 컨테이너에 대해 성능 정보 수집
        for (String containerName : targetContainerNames) {
            DockerContainerStatus dockerStatus = containerStatusMap.get(containerName);
            boolean containerRunning = dockerStatus != null && dockerStatus.running();

            // 서비스 이름 결정: monitoredServices에 있으면 serviceName 사용, 없으면 containerName 사용
            String serviceName = monitoredServices.stream()
                .filter(target -> target.containerName().equals(containerName) ||
                    containerName.contains(target.containerName()) ||
                    containerName.contains(target.serviceName()))
                .findFirst()
                .map(ServiceTarget::serviceName)
                .orElse(containerName);

            CpuMemUsage usage = containerRunning
                ? usageMap.getOrDefault(containerName, CpuMemUsage.unavailable())
                : CpuMemUsage.unavailable();
            Optional<Double> loadAvgOptional = containerRunning
                ? fetchLoadAverage(containerName)
                : Optional.empty();

            boolean statsAvailable = usage.available();
            boolean loadAvailable = loadAvgOptional.isPresent();

            if (containerRunning) {
                if (!statsAvailable) {
                    log.warn("컨테이너 '{}'에 대한 docker stats 정보를 가져오지 못했습니다.", containerName);
                }
                if (!loadAvailable) {
                    log.warn("컨테이너 '{}'에 대한 load average 정보를 가져오지 못했습니다.", containerName);
                }
            }

            double cpuPercent = statsAvailable ? round(usage.cpuUsage(), 1) : 0.0;
            double memoryPercent = statsAvailable ? round(usage.memoryUsage(), 1) : 0.0;
            double compositeScore = containerRunning
                ? round(calculateCompositeScore(cpuPercent, memoryPercent), 2)
                : 0.0;
            String status;
            if (containerRunning) {
                status = determineStatus(compositeScore);
            } else {
                status = "EXITED";
            }
            double loadAvg = loadAvailable ? round(loadAvgOptional.orElse(0.0), 2) : 0.0;

            services.add(ServicePerformanceInfoResponse.builder()
                .serviceName(
                    serviceName)  // 서비스 이름 사용 (monitoredServices에 있으면 serviceName, 없으면 containerName)
                .loadAvg1m(loadAvg)
                .cpuUsagePercent(cpuPercent)
                .memoryUsagePercent(memoryPercent)
                .compositeScore(compositeScore)
                .status(status)
                .build());
        }

        int serviceCount = services.size();
        log.info("모니터링 대상 서비스 성능 정보 수집 완료: {}개", serviceCount);

        return ServicePerformanceListResponse.builder()
            .timestamp(getKstTimestamp())
            .services(services)
            .build();
    }

    public int getMonitoredServiceCount() {
        return monitoredServices.isEmpty() ? 0 : monitoredServices.size();
    }

    private Map<String, CpuMemUsage> fetchCpuMemStats(List<String> containerNames) {
        Map<String, CpuMemUsage> result = new HashMap<>();
        if (containerNames.isEmpty()) {
            return result;
        }

        List<String> command = new ArrayList<>();
        command.add("docker");
        command.add("stats");
        command.add("--no-stream");
        command.add("--format");
        command.add("{{.Name}};{{.CPUPerc}};{{.MemPerc}}");
        command.addAll(containerNames);

        Process process = null;
        try {
            process = new ProcessBuilder(command).start();
            boolean finished = process.waitFor(5, TimeUnit.SECONDS);
            if (!finished) {
                process.destroyForcibly();
                process.waitFor(1, TimeUnit.SECONDS);
                log.warn("docker stats 명령이 시간 내에 종료되지 않았습니다. command={}", command);
            }

            String stdout = readStream(process.getInputStream());
            String stderr = readStream(process.getErrorStream());

            if (finished && process.exitValue() != 0) {
                log.warn("docker stats 명령이 실패했습니다. exitCode={}, stderr={}",
                    process.exitValue(), stderr.trim());
            }

            stdout.lines()
                .map(String::trim)
                .filter(line -> !line.isEmpty())
                .forEach(line -> {
                    String[] parts = line.split(";");
                    if (parts.length < 3) {
                        log.warn("docker stats 출력 파싱 실패: {}", line);
                        return;
                    }
                    String containerName = parts[0].trim();
                    double cpu = parsePercent(parts[1]);
                    double mem = parsePercent(parts[2]);
                    result.put(containerName, new CpuMemUsage(cpu, mem, true));
                });
        } catch (IOException e) {
            log.error("docker stats 명령 실행 중 IO 예외가 발생했습니다.", e);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            log.warn("docker stats 명령 대기 중 인터럽트가 발생했습니다.", e);
        } finally {
            if (process != null) {
                process.destroy();
            }
        }

        containerNames.stream()
            .filter(name -> !result.containsKey(name))
            .forEach(name -> result.put(name, CpuMemUsage.unavailable()));

        return result;
    }

    private Optional<Double> fetchLoadAverage(String containerName) {
        Process process = null;
        try {
            process = new ProcessBuilder("docker", "exec", containerName, "cat", "/proc/loadavg")
                .start();
            boolean finished = process.waitFor(3, TimeUnit.SECONDS);
            if (!finished) {
                process.destroyForcibly();
                process.waitFor(1, TimeUnit.SECONDS);
                log.warn("docker exec loadavg 명령이 시간 내에 종료되지 않았습니다. container={}",
                    containerName);
                return Optional.empty();
            }

            String stdout = readStream(process.getInputStream());
            String stderr = readStream(process.getErrorStream());
            int exitCode = process.exitValue();
            if (exitCode != 0) {
                log.warn("docker exec loadavg 명령이 실패했습니다. container={}, exitCode={}, stderr={}",
                    containerName, exitCode, stderr.trim());
                return Optional.empty();
            }

            if (stdout.isBlank()) {
                return Optional.empty();
            }

            String[] parts = stdout.trim().split("\\s+");
            if (parts.length == 0) {
                return Optional.empty();
            }

            return Optional.of(Double.parseDouble(parts[0]));
        } catch (IOException e) {
            log.error("docker exec loadavg 명령 실행 중 IO 예외가 발생했습니다. container={}",
                containerName, e);
            return Optional.empty();
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            log.warn("docker exec loadavg 명령 대기 중 인터럽트가 발생했습니다. container={}",
                containerName, e);
            return Optional.empty();
        } catch (NumberFormatException e) {
            log.warn("load average 파싱 실패: container={}, value={}", containerName, e.getMessage());
            return Optional.empty();
        } finally {
            if (process != null) {
                process.destroy();
            }
        }
    }

    private Map<String, DockerContainerStatus> getAllContainers() {
        Map<String, DockerContainerStatus> result = new HashMap<>();
        Process process = null;
        try {
            process = new ProcessBuilder("docker", "ps", "-a", "--format", "{{.Names}};{{.Status}}")
                .start();
            boolean finished = process.waitFor(3, TimeUnit.SECONDS);
            if (!finished) {
                process.destroyForcibly();
                process.waitFor(1, TimeUnit.SECONDS);
                log.warn("docker ps 명령이 시간 내에 종료되지 않았습니다.");
                return result;
            }

            String stdout = readStream(process.getInputStream());
            String stderr = readStream(process.getErrorStream());
            int exitCode = process.exitValue();
            if (exitCode != 0) {
                log.warn("docker ps 명령이 실패했습니다. exitCode={}, stderr={}", exitCode, stderr.trim());
                return result;
            }

            if (stdout.isBlank()) {
                log.warn("docker ps 명령의 출력이 비어 있습니다. 실행 중인 컨테이너가 없거나 권한 문제일 수 있습니다.");
                return result;
            }

            log.debug("docker ps 출력:\n{}", stdout);

            stdout.lines()
                .map(String::trim)
                .filter(line -> !line.isEmpty())
                .forEach(line -> {
                    String[] parts = line.split(";", 2);
                    if (parts.length == 0) {
                        log.warn("docker ps 출력 파싱 실패: 빈 라인");
                        return;
                    }
                    String containerName = parts[0].trim();
                    String statusText = parts.length > 1 ? parts[1].trim() : "";
                    boolean running = statusText.toLowerCase().startsWith("up");
                    log.debug("컨테이너 파싱: name={}, status={}, running={}", containerName, statusText,
                        running);
                    result.put(containerName,
                        new DockerContainerStatus(containerName, statusText, running));
                });
        } catch (IOException e) {
            log.error("docker ps 명령 실행 중 IO 예외가 발생했습니다.", e);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            log.warn("docker ps 명령 대기 중 인터럽트가 발생했습니다.", e);
        } finally {
            if (process != null) {
                process.destroy();
            }
        }
        return result;
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

    private double parsePercent(String raw) {
        if (raw == null || raw.isBlank()) {
            return 0.0;
        }
        String cleaned = raw.replace("%", "").trim();
        if (cleaned.isEmpty()) {
            return 0.0;
        }
        try {
            return Double.parseDouble(cleaned);
        } catch (NumberFormatException e) {
            log.warn("백분율 파싱 실패: {}", raw);
            return 0.0;
        }
    }

    private String readStream(InputStream stream) throws IOException {
        if (stream == null) {
            return "";
        }
        try (InputStream in = stream;
            BufferedReader reader = new BufferedReader(
                new InputStreamReader(in, StandardCharsets.UTF_8))) {
            StringBuilder sb = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) {
                sb.append(line).append('\n');
            }
            return sb.toString();
        }
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

        return MemoryUsageResponse.builder()
            .timestamp(getKstTimestamp())
            .totalMemoryGB(totalMemoryGb)
            .usedMemoryGB(usedMemoryGb)
            .memoryUsagePercent(memoryUsagePercent)
            .build();
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

                // 더 관대한 필터링: UP 상태이거나 UNKNOWN 상태이고, 속도가 0보다 큰 경우
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

    private NetworkTrafficResponse getNetworkData(
        long bytesSent,
        long bytesRecv,
        double bandwidthMbps,
        double intervalSeconds
    ) {
        double inboundMbps = bytesToMbps(bytesRecv, intervalSeconds);
        double outboundMbps = bytesToMbps(bytesSent, intervalSeconds);

        return NetworkTrafficResponse.builder()
            .timestamp(getKstTimestamp())
            .inboundMbps(inboundMbps)
            .outboundMbps(outboundMbps)
            .bandwidthMbps(bandwidthMbps)
            .build();
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
            NetworkTrafficResponse trafficData = NetworkTrafficResponse.builder()
                .timestamp(getKstTimestamp())
                .inboundMbps(inboundMbps)
                .outboundMbps(outboundMbps)
                .bandwidthMbps(bandwidthMbps)
                .build();

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
                            data = NetworkTrafficResponse.builder()
                                .timestamp(getKstTimestamp())
                                .inboundMbps(0.0)
                                .outboundMbps(0.0)
                                .bandwidthMbps(bandwidthMbps)
                                .build();
                        }
                    } else {
                        // Redis에 데이터가 없으면 기본값 반환
                        data = NetworkTrafficResponse.builder()
                            .timestamp(getKstTimestamp())
                            .inboundMbps(0.0)
                            .outboundMbps(0.0)
                            .bandwidthMbps(bandwidthMbps)
                            .build();
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
                        return NetworkTrafficResponse.builder()
                            .timestamp(getKstTimestamp())
                            .inboundMbps(0.0)
                            .outboundMbps(0.0)
                            .bandwidthMbps(bandwidthMbps)
                            .build();
                    })
                    .map(data -> ServerSentEvent.<NetworkTrafficResponse>builder()
                        .event("update")
                        .data(data)
                        .build())
            ).doOnCancel(() -> log.info("네트워크 트래픽 스트리밍이 취소되었습니다."))
            .doOnError(error -> log.error("네트워크 트래픽 스트리밍 중 오류 발생", error));
    }

    private String formatSseEvent(String eventType, Object data) {
        try {
            String jsonData = objectMapper.writeValueAsString(data);
            return String.format("event: %s\ndata: %s\n\n", eventType, jsonData);
        } catch (JsonProcessingException e) {
            log.error("SSE 이벤트 포맷팅 중 오류 발생", e);
            return String.format("event: error\ndata: {\"error\":\"%s\"}\n\n", e.getMessage());
        }
    }
}
