package com.ssafy.hebees.monitoring.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.ssafy.hebees.monitoring.dto.response.CpuUsageResponse;
import com.ssafy.hebees.common.util.MonitoringUtils;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import oshi.SystemInfo;
import oshi.hardware.CentralProcessor;
import oshi.hardware.CentralProcessor.TickType;
import oshi.hardware.HardwareAbstractionLayer;
import org.springframework.beans.factory.annotation.Qualifier;
import com.ssafy.hebees.common.util.RedisStreamUtils;
import org.springframework.data.redis.connection.stream.MapRecord;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.http.codec.ServerSentEvent;
import org.springframework.scheduling.annotation.Async;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Flux;
import reactor.core.scheduler.Schedulers;

import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.Map;

@Slf4j
@Service
@RequiredArgsConstructor
public class CpuMonitoringService {

    @Qualifier("monitoringRedisTemplate")
    private final StringRedisTemplate monitoringRedisTemplate;
    private final ObjectMapper objectMapper = new ObjectMapper();

    private final SystemInfo systemInfo = new SystemInfo();
    private final HardwareAbstractionLayer hal = systemInfo.getHardware();

    // CPU ticks cache
    private volatile boolean cpuTicksInitialized = false;
    private volatile long[] previousCpuTicks = null;
    private final Object cpuTicksLock = new Object();

    private int calculateActiveCores(int totalCores, double cpuPercent) {
        return (int) Math.round(totalCores * cpuPercent / 100.0);
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
            long diff = Math.max(0, currentTicks[i] - previousTicks[i]);
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
            MonitoringUtils.getKstTimestamp(),
            MonitoringUtils.round(cpuPercent, 1),
            totalCores,
            activeCores
        );
    }

    @Scheduled(fixedRate = 1000)
    @Async
    public void collectCpuData() {
        try {
            CpuUsageResponse cpuData = getCpuData();
            String jsonData = objectMapper.writeValueAsString(cpuData);

            Map<String, String> record = Collections.singletonMap("data", jsonData);
            RedisStreamUtils.addRecord(monitoringRedisTemplate, MonitoringUtils.CPU_STREAM_KEY,
                record);

            // Stream 크기 제한 (최근 1000개만 유지)
            RedisStreamUtils.trimStream(monitoringRedisTemplate, MonitoringUtils.CPU_STREAM_KEY,
                1000, false);
        } catch (JsonProcessingException e) {
            log.error("CPU 데이터 직렬화 실패", e);
        } catch (Exception e) {
            log.error("CPU 데이터 수집 중 오류 발생", e);
        }
    }

    /**
     * Redis Stream에서 CPU 이벤트를 읽어옵니다.
     */
    public List<MapRecord<String, String, String>> readEvents(String lastId, long blockMillis,
        Long count) {
        return RedisStreamUtils.readEvents(
            monitoringRedisTemplate,
            MonitoringUtils.CPU_STREAM_KEY,
            lastId,
            blockMillis,
            count);
    }

    public Flux<ServerSentEvent<CpuUsageResponse>> streamCpuUsage() {
        // 초기 스냅샷 조회
        CpuUsageResponse initialData = getCpuData();
        String lastId = null;

        // Stream에서 최신 레코드 ID 조회
        try {
            lastId = RedisStreamUtils.getLatestRecordId(monitoringRedisTemplate,
                MonitoringUtils.CPU_STREAM_KEY);
        } catch (Exception e) {
            log.warn("초기 CPU Stream ID 조회 실패", e);
        }

        // Stream이 비어있으면 "$" 사용 (최신 이후의 신규 메시지만 읽기)
        // Stream에 데이터가 있으면 마지막 ID 사용 (그 이후의 메시지 읽기)
        final String initialLastId = lastId != null ? lastId : "$";

        return Flux.concat(
                Flux.just(ServerSentEvent.<CpuUsageResponse>builder()
                    .event("init")
                    .data(initialData)
                    .build()),
                Flux.<CpuUsageResponse>create(sink -> {
                        java.util.concurrent.atomic.AtomicReference<String> currentLastIdRef =
                            new java.util.concurrent.atomic.AtomicReference<>(initialLastId);
                        boolean[] cancelled = new boolean[]{false};

                        // 블로킹 읽기를 별도 스레드에서 실행
                        Schedulers.boundedElastic().schedule(() -> {
                            while (!cancelled[0] && !sink.isCancelled()) {
                                try {
                                    // 블로킹 읽기 (1초 대기)
                                    List<MapRecord<String, String, String>> records = readEvents(
                                        currentLastIdRef.get(), 1000L, 10L);
                                    if (records != null && !records.isEmpty()) {
                                        for (MapRecord<String, String, String> record : records) {
                                            if (cancelled[0] || sink.isCancelled()) {
                                                break;
                                            }
                                            String jsonData = record.getValue().get("data");
                                            if (jsonData != null) {
                                                try {
                                                    CpuUsageResponse data = objectMapper.readValue(
                                                        jsonData, CpuUsageResponse.class);
                                                    sink.next(data);
                                                    currentLastIdRef.set(record.getId().getValue());
                                                } catch (JsonProcessingException e) {
                                                    log.warn("CPU Stream 데이터 파싱 실패", e);
                                                }
                                            }
                                        }
                                    }
                                    // 새로운 메시지가 없으면 블로킹 읽기가 다시 대기
                                } catch (Exception e) {
                                    log.warn("CPU Stream 읽기 중 오류 발생", e);
                                    // 오류 발생 시에도 계속 시도
                                }
                            }
                            sink.complete();
                        });

                        sink.onCancel(() -> {
                            cancelled[0] = true;
                            log.info("CPU 사용률 스트리밍이 취소되었습니다.");
                        });
                    })
                    .map(data -> ServerSentEvent.<CpuUsageResponse>builder()
                        .event("update")
                        .data(data)
                        .build())
            )
            .doOnError(error -> log.error("CPU 사용률 스트리밍 중 오류 발생", error));
    }
}

