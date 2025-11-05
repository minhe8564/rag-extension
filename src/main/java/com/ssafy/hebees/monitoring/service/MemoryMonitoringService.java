package com.ssafy.hebees.monitoring.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.ssafy.hebees.monitoring.dto.response.MemoryUsageResponse;
import com.ssafy.hebees.common.util.MonitoringUtils;
import lombok.extern.slf4j.Slf4j;
import oshi.SystemInfo;
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

import java.time.Duration;
import java.util.Collections;
import java.util.List;
import java.util.Map;

@Slf4j
@Service
public class MemoryMonitoringService {

    private final StringRedisTemplate monitoringRedisTemplate;
    private final ObjectMapper objectMapper = new ObjectMapper();

    private final SystemInfo systemInfo = new SystemInfo();
    private final HardwareAbstractionLayer hal = systemInfo.getHardware();

    public MemoryMonitoringService(
        @Qualifier("monitoringRedisTemplate") StringRedisTemplate monitoringRedisTemplate) {
        this.monitoringRedisTemplate = monitoringRedisTemplate;
    }

    private double calculateMemoryUsagePercent(double usedGb, double totalGb) {
        if (totalGb == 0) {
            return 0.0;
        }
        return MonitoringUtils.round((usedGb / totalGb) * 100.0, 1);
    }

    public MemoryUsageResponse getMemoryData() {
        oshi.hardware.GlobalMemory memory = hal.getMemory();
        double totalMemoryGb = MonitoringUtils.bytesToGb(memory.getTotal());
        double usedMemoryGb = MonitoringUtils.bytesToGb(memory.getTotal() - memory.getAvailable());
        double memoryUsagePercent = calculateMemoryUsagePercent(usedMemoryGb, totalMemoryGb);

        return new MemoryUsageResponse(
            MonitoringUtils.getKstTimestamp(),
            totalMemoryGb,
            usedMemoryGb,
            memoryUsagePercent
        );
    }

    @Scheduled(fixedRate = 1000)
    @Async
    public void collectMemoryData() {
        try {
            MemoryUsageResponse memoryData = getMemoryData();
            String jsonData = objectMapper.writeValueAsString(memoryData);

            Map<String, String> record = Collections.singletonMap("data", jsonData);
            RedisStreamUtils.addRecord(monitoringRedisTemplate, MonitoringUtils.MEMORY_STREAM_KEY,
                record);

            // Stream 크기 제한 (최근 1000개만 유지)
            RedisStreamUtils.trimStream(monitoringRedisTemplate, MonitoringUtils.MEMORY_STREAM_KEY,
                1000, false);
        } catch (JsonProcessingException e) {
            log.error("메모리 데이터 직렬화 실패", e);
        } catch (Exception e) {
            log.error("메모리 데이터 수집 중 오류 발생", e);
        }
    }

    /**
     * Redis Stream에서 메모리 이벤트를 읽어옵니다.
     */
    public List<MapRecord<String, String, String>> readEvents(String lastId, long blockMillis,
        Long count) {
        return RedisStreamUtils.readEvents(
            monitoringRedisTemplate,
            MonitoringUtils.MEMORY_STREAM_KEY,
            lastId,
            blockMillis,
            count);
    }

    public Flux<ServerSentEvent<MemoryUsageResponse>> streamMemoryUsage() {
        // 초기 스냅샷 조회
        MemoryUsageResponse initialData = getMemoryData();
        String lastId = null;

        // Stream에서 최신 레코드 ID 조회
        try {
            lastId = RedisStreamUtils.getLatestRecordId(monitoringRedisTemplate,
                MonitoringUtils.MEMORY_STREAM_KEY);
        } catch (Exception e) {
            log.warn("초기 메모리 Stream ID 조회 실패", e);
        }

        final String initialLastId = lastId != null ? lastId : "$";

        return Flux.concat(
                Flux.just(ServerSentEvent.<MemoryUsageResponse>builder()
                    .event("init")
                    .data(initialData)
                    .build()),
                Flux.<MemoryUsageResponse>create(sink -> {
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
                                                    MemoryUsageResponse data = objectMapper.readValue(
                                                        jsonData, MemoryUsageResponse.class);
                                                    sink.next(data);
                                                    currentLastIdRef.set(record.getId().getValue());
                                                } catch (JsonProcessingException e) {
                                                    log.warn("메모리 Stream 데이터 파싱 실패", e);
                                                }
                                            }
                                        }
                                    }
                                    // 새로운 메시지가 없으면 블로킹 읽기가 다시 대기
                                } catch (Exception e) {
                                    log.warn("메모리 Stream 읽기 중 오류 발생", e);
                                    // 오류 발생 시에도 계속 시도
                                }
                            }
                            sink.complete();
                        });

                        sink.onCancel(() -> {
                            cancelled[0] = true;
                            log.info("메모리 사용률 스트리밍이 취소되었습니다.");
                        });
                    })
                    .map(data -> ServerSentEvent.<MemoryUsageResponse>builder()
                        .event("update")
                        .data(data)
                        .build())
            )
            .doOnError(error -> log.error("메모리 사용률 스트리밍 중 오류 발생", error));
    }
}

