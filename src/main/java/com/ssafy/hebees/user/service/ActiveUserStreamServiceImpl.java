package com.ssafy.hebees.user.service;

import com.ssafy.hebees.common.util.MonitoringUtils;
import com.ssafy.hebees.common.util.RedisStreamUtils;
import com.ssafy.hebees.monitoring.service.ActiveUserService;
import jakarta.annotation.PostConstruct;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.data.redis.connection.stream.MapRecord;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.util.List;
import java.util.Set;
import java.util.concurrent.CopyOnWriteArraySet;

@Slf4j
@Service
@RequiredArgsConstructor
public class ActiveUserStreamServiceImpl implements ActiveUserStreamService {

    @Qualifier("activeUserRedisTemplate")
    private final StringRedisTemplate activeUserRedisTemplate;
    private final ActiveUserService activeUserService;
    private final Set<SseEmitter> emitters = new CopyOnWriteArraySet<>();
    private volatile String lastReadId = null;
    private volatile long lastBroadcastCount = -1;

    @PostConstruct
    void initialize() {
        // 최신 레코드 ID로 초기화
        lastReadId = RedisStreamUtils.getLatestRecordId(
            activeUserRedisTemplate,
            MonitoringUtils.ACTIVE_USER_STREAM_KEY
        );
    }

    @Override
    public SseEmitter subscribeActiveUsers(String lastEventId) {
        SseEmitter emitter = new SseEmitter(0L); // 타임아웃 없음
        emitters.add(emitter);

        emitter.onCompletion(() -> removeEmitter(emitter));
        emitter.onTimeout(() -> removeEmitter(emitter));
        emitter.onError(throwable -> removeEmitter(emitter));

        // 초기 활성 사용자 수 전송
        long currentCount = activeUserService.getActiveUserCount();
        lastBroadcastCount = currentCount; // 초기값 설정
        sendDataEvent(emitter, "init", currentCount);

        log.debug("Subscribed to active users stream (lastEventId={}), initialCount={}",
            lastEventId, currentCount);
        return emitter;
    }

    /**
     * 주기적으로 활성 사용자 수를 확인하고 변경 시 브로드캐스트 2초마다 실행
     */
    @Scheduled(fixedRate = 2000)
    public void pollAndBroadcast() {
        if (emitters.isEmpty()) {
            return;
        }

        try {
            // 현재 활성 사용자 수 조회
            long currentCount = activeUserService.getActiveUserCount();

            // 활성 사용자 수가 변경되었을 때만 브로드캐스트
            if (currentCount != lastBroadcastCount) {
                log.debug("활성 사용자 수 변경 감지: {} -> {}", lastBroadcastCount, currentCount);
                lastBroadcastCount = currentCount;
                broadcastUpdate(currentCount);
            }

            // Redis Stream에서 새 이벤트 읽기 (선택적 - 로깅용)
            List<MapRecord<String, String, String>> records = RedisStreamUtils.readEvents(
                activeUserRedisTemplate,
                MonitoringUtils.ACTIVE_USER_STREAM_KEY,
                lastReadId,
                0, // non-blocking
                100L // 최대 100개
            );

            if (!records.isEmpty()) {
                // 최신 레코드 ID 업데이트
                lastReadId = records.get(records.size() - 1).getId().getValue();
                log.debug("Redis Stream에서 {}개의 새 이벤트 읽음", records.size());
            }
        } catch (Exception e) {
            log.warn("활성 사용자 수 브로드캐스트 실패: {}", e.getMessage());
        }
    }

    private void broadcastUpdate(long count) {
        for (SseEmitter emitter : emitters) {
            sendDataEvent(emitter, "update", count);
        }
    }

    private void sendDataEvent(SseEmitter emitter, String eventName, long count) {
        try {
            emitter.send(SseEmitter.event()
                .id(Long.toString(count))
                .name(eventName)
                .data(count));
        } catch (Exception e) {
            log.debug("SSE send failed: {}", e.getMessage());
            removeEmitter(emitter);
            emitter.completeWithError(e);
        }
    }

    private void removeEmitter(SseEmitter emitter) {
        emitters.remove(emitter);
        log.debug("Removed emitter. Remaining subscribers: {}", emitters.size());
    }
}
