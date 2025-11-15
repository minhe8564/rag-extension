package com.ssafy.hebees.monitoring.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.ssafy.hebees.monitoring.config.MonitoringProperties;
import com.ssafy.hebees.monitoring.dto.response.NetworkTrafficResponse;
import com.ssafy.hebees.common.util.HostIdentifierResolver;
import com.ssafy.hebees.common.util.MonitoringUtils;
import lombok.extern.slf4j.Slf4j;
import oshi.SystemInfo;
import oshi.hardware.HardwareAbstractionLayer;
import oshi.hardware.NetworkIF;
import org.springframework.beans.factory.annotation.Qualifier;
import jakarta.annotation.PostConstruct;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import com.ssafy.hebees.common.util.RedisStreamUtils;
import org.springframework.data.redis.connection.stream.MapRecord;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.http.codec.ServerSentEvent;
import org.springframework.scheduling.annotation.Async;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Flux;
import reactor.core.scheduler.Schedulers;

@Slf4j
@Service
public class NetworkMonitoringService {

    private final SystemInfo systemInfo = new SystemInfo();
    private final HardwareAbstractionLayer hal = systemInfo.getHardware();
    private final ObjectMapper objectMapper = new ObjectMapper();
    private final StringRedisTemplate monitoringRedisTemplate;
    private final MonitoringProperties monitoringProperties;
    private final HostIdentifierResolver hostIdentifierResolver;
    private String networkBytesKey;
    private String networkStreamKey;

    // Network bandwidth cache
    private volatile Double cachedBandwidthMbps = null;
    private final Object bandwidthLock = new Object();

    public NetworkMonitoringService(
        @Qualifier("monitoringRedisTemplate") StringRedisTemplate monitoringRedisTemplate,
        MonitoringProperties monitoringProperties,
        HostIdentifierResolver hostIdentifierResolver) {
        this.monitoringRedisTemplate = monitoringRedisTemplate;
        this.monitoringProperties = monitoringProperties;
        this.hostIdentifierResolver = hostIdentifierResolver;
    }

    @PostConstruct
    void initNetworkKeys() {
        String hostIdentifier = hostIdentifierResolver.resolveHostIdentifier();
        networkBytesKey = MonitoringUtils.buildNetworkBytesKey(hostIdentifier);
        networkStreamKey = MonitoringUtils.buildStreamKey(MonitoringUtils.NETWORK_STREAM_KEY,
            hostIdentifier);
        log.debug("Initialized network bytes Redis key: {}", networkBytesKey);
        log.debug("Initialized network stream Redis key: {}", networkStreamKey);
    }

    private String getNetworkBytesKey() {
        if (networkBytesKey == null) {
            String hostIdentifier = hostIdentifierResolver.resolveHostIdentifier();
            networkBytesKey = MonitoringUtils.buildNetworkBytesKey(hostIdentifier);
        }
        return networkBytesKey;
    }

    private String getNetworkStreamKey() {
        if (networkStreamKey == null) {
            String hostIdentifier = hostIdentifierResolver.resolveHostIdentifier();
            networkStreamKey = MonitoringUtils.buildStreamKey(MonitoringUtils.NETWORK_STREAM_KEY,
                hostIdentifier);
        }
        return networkStreamKey;
    }

    private double getNetworkBandwidthMbps() {
        return monitoringProperties.getNetworkBandwidthMbps();
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
                boolean isNotLoopback = !name.toLowerCase().contains("lo") &&
                    !name.toLowerCase().contains("loopback") &&
                    !name.toLowerCase().startsWith("veth") &&
                    !name.toLowerCase().startsWith("docker");

                if (isUp && hasSpeed && isNotLoopback) {
                    double speedMbps = speed / 1_000_000.0;

                    if (speedMbps > 1_000_000) {
                        log.debug("인터페이스 '{}' 속도가 비현실적으로 큼: {} Mbps (원본: {} bps), 무시함",
                            name, speedMbps, speed);
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
            return MonitoringUtils.round(maxSpeedMbps, 1);
        } else {
            log.warn("네트워크 대역폭 자동 감지 실패: 감지된 인터페이스가 없습니다. 설정값 사용: {} Mbps",
                getNetworkBandwidthMbps());
            return getNetworkBandwidthMbps();
        }
    }

    private double getNetworkBandwidth() {
        if (cachedBandwidthMbps != null) {
            return cachedBandwidthMbps;
        }

        synchronized (bandwidthLock) {
            if (cachedBandwidthMbps != null) {
                return cachedBandwidthMbps;
            }

            double detectedBandwidth = detectNetworkBandwidth();
            if (detectedBandwidth > 0) {
                cachedBandwidthMbps = detectedBandwidth;
                log.info("네트워크 대역폭 감지 완료 및 캐시: {} Mbps", detectedBandwidth);
                return detectedBandwidth;
            }

            log.info("설정값 사용: {} Mbps", getNetworkBandwidthMbps());
            cachedBandwidthMbps = getNetworkBandwidthMbps();
            return getNetworkBandwidthMbps();
        }
    }

    @Scheduled(fixedRate = 5000)
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

            String previousBytesData = monitoringRedisTemplate.opsForValue()
                .get(getNetworkBytesKey());
            long previousBytesSent = 0;
            long previousBytesRecv = 0;
            double inboundMbps = 0.0;
            double outboundMbps = 0.0;

            if (previousBytesData != null) {
                try {
                    String[] parts = previousBytesData.split(",");
                    if (parts.length == 2) {
                        previousBytesSent = Long.parseLong(parts[0]);
                        previousBytesRecv = Long.parseLong(parts[1]);

                        long bytesSentDiff = totalBytesSent - previousBytesSent;
                        long bytesRecvDiff = totalBytesRecv - previousBytesRecv;

                        inboundMbps = MonitoringUtils.bytesToMbps(bytesRecvDiff, 5.0);
                        outboundMbps = MonitoringUtils.bytesToMbps(bytesSentDiff, 5.0);
                    }
                } catch (Exception e) {
                    log.warn("이전 네트워크 bytes 데이터 파싱 실패", e);
                }
            }

            String currentBytesData = totalBytesSent + "," + totalBytesRecv;
            monitoringRedisTemplate.opsForValue()
                .set(getNetworkBytesKey(), currentBytesData);

            NetworkTrafficResponse trafficData = new NetworkTrafficResponse(
                MonitoringUtils.getKstTimestamp(),
                inboundMbps,
                outboundMbps,
                bandwidthMbps
            );

            try {
                String jsonData = objectMapper.writeValueAsString(trafficData);

                // Redis Stream에 추가 (호스트별 Stream 키 사용)
                Map<String, String> record = Collections.singletonMap("data", jsonData);
                RedisStreamUtils.addRecord(monitoringRedisTemplate,
                    getNetworkStreamKey(), record);

                // Stream 크기 제한 (최근 1000개만 유지)
                RedisStreamUtils.trimStream(monitoringRedisTemplate,
                    getNetworkStreamKey(), 1000, false);

                log.debug("네트워크 트래픽 데이터 저장 완료: inbound={}, outbound={}", inboundMbps, outboundMbps);
            } catch (JsonProcessingException e) {
                log.error("네트워크 트래픽 데이터 저장 실패", e);
            }
        } catch (Exception e) {
            log.error("네트워크 트래픽 수집 중 오류 발생", e);
        }
    }

    /**
     * Redis Stream에서 네트워크 이벤트를 읽어옵니다.
     */
    public List<MapRecord<String, String, String>> readEvents(String lastId, long blockMillis,
        Long count) {
        return RedisStreamUtils.readEvents(
            monitoringRedisTemplate,
            getNetworkStreamKey(),
            lastId,
            blockMillis,
            count);
    }

    public Flux<ServerSentEvent<NetworkTrafficResponse>> streamNetworkTraffic() {
        double bandwidthMbps = getNetworkBandwidth();

        // 초기 스냅샷 조회 (Stream에서 최신 레코드 또는 기본값)
        NetworkTrafficResponse initialData;
        String lastId = null;

        try {
            List<MapRecord<String, String, String>> records = RedisStreamUtils.getLatestRecords(
                monitoringRedisTemplate, getNetworkStreamKey(), 1L);
            if (records != null && !records.isEmpty()) {
                MapRecord<String, String, String> latestRecord = records.get(0);
                lastId = latestRecord.getId().getValue();
                String jsonData = latestRecord.getValue().get("data");
                if (jsonData != null) {
                    try {
                        initialData = objectMapper.readValue(jsonData,
                            NetworkTrafficResponse.class);
                    } catch (JsonProcessingException e) {
                        log.warn("초기 네트워크 데이터 파싱 실패", e);
                        initialData = new NetworkTrafficResponse(
                            MonitoringUtils.getKstTimestamp(), 0.0, 0.0, bandwidthMbps);
                    }
                } else {
                    initialData = new NetworkTrafficResponse(
                        MonitoringUtils.getKstTimestamp(), 0.0, 0.0, bandwidthMbps);
                }
            } else {
                initialData = new NetworkTrafficResponse(
                    MonitoringUtils.getKstTimestamp(), 0.0, 0.0, bandwidthMbps);
            }
        } catch (Exception e) {
            log.warn("초기 네트워크 Stream ID 조회 실패", e);
            initialData = new NetworkTrafficResponse(
                MonitoringUtils.getKstTimestamp(), 0.0, 0.0, bandwidthMbps);
        }

        final String initialLastId = lastId != null ? lastId : "$";

        return Flux.concat(
                Flux.just(ServerSentEvent.<NetworkTrafficResponse>builder()
                    .event("init")
                    .data(initialData)
                    .build()),
                Flux.<NetworkTrafficResponse>create(sink -> {
                        java.util.concurrent.atomic.AtomicReference<String> currentLastIdRef =
                            new java.util.concurrent.atomic.AtomicReference<>(initialLastId);
                        boolean[] cancelled = new boolean[]{false};

                        // 블로킹 읽기를 별도 스레드에서 실행
                        Schedulers.boundedElastic().schedule(() -> {
                            while (!cancelled[0] && !sink.isCancelled()) {
                                try {
                                    // 블로킹 읽기 (5초 대기)
                                    List<MapRecord<String, String, String>> records = readEvents(
                                        currentLastIdRef.get(), 5000L, 10L);
                                    if (records != null && !records.isEmpty()) {
                                        for (MapRecord<String, String, String> record : records) {
                                            if (cancelled[0] || sink.isCancelled()) {
                                                break;
                                            }
                                            String jsonData = record.getValue().get("data");
                                            if (jsonData != null) {
                                                try {
                                                    NetworkTrafficResponse data = objectMapper.readValue(
                                                        jsonData, NetworkTrafficResponse.class);
                                                    sink.next(data);
                                                    currentLastIdRef.set(record.getId().getValue());
                                                } catch (JsonProcessingException e) {
                                                    log.warn("네트워크 Stream 데이터 파싱 실패", e);
                                                }
                                            }
                                        }
                                    }
                                    // 새로운 메시지가 없으면 블로킹 읽기가 다시 대기
                                } catch (Exception e) {
                                    log.warn("네트워크 Stream 읽기 중 오류 발생", e);
                                    // 오류 발생 시에도 계속 시도
                                }
                            }
                            sink.complete();
                        });

                        sink.onCancel(() -> {
                            cancelled[0] = true;
                            log.info("네트워크 트래픽 스트리밍이 취소되었습니다.");
                        });
                    })
                    .map(data -> ServerSentEvent.<NetworkTrafficResponse>builder()
                        .event("update")
                        .data(data)
                        .build())
            )
            .doOnError(error -> log.error("네트워크 트래픽 스트리밍 중 오류 발생", error));
    }
}
