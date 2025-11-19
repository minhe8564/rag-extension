package com.ssafy.hebees.common.subscriber;

import com.ssafy.hebees.common.util.RedisStreamUtils;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.concurrent.atomic.AtomicReference;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.connection.stream.MapRecord;
import org.springframework.data.redis.core.StringRedisTemplate;

/**
 * Redis Stream 구독에 필요한 공통 로직을 제공하는 추상 클래스.
 * 컨슈머 그룹을 사용하지 않고 일반 XREAD를 사용합니다.
 */
@Slf4j
public abstract class BaseRedisStreamSubscriber {

    private final String streamKey;
    private final String logPrefix;
    private final StringRedisTemplate redisTemplate;

    // 마지막 읽은 레코드 ID를 추적 (서버 재시작 시 초기화됨)
    private final AtomicReference<String> lastReadId = new AtomicReference<>("$");

    protected BaseRedisStreamSubscriber(
        StringRedisTemplate redisTemplate,
        String streamKey,
        String logPrefix
    ) {
        this.redisTemplate = Objects.requireNonNull(redisTemplate,
            "redisTemplate must not be null");
        this.streamKey = Objects.requireNonNull(streamKey,
            "streamKey must not be null");
        this.logPrefix = logPrefix != null ? logPrefix : "STREAM";
    }

    /**
     * 주기적으로 호출되어 Redis Stream에서 메시지를 소비한다.
     * 컨슈머 그룹을 사용하지 않고 일반 XREAD를 사용합니다.
     */
    protected void pollStreamInternal() {
        try {
            String currentLastId = lastReadId.get();
            String currentStreamKey = Objects.requireNonNull(streamKey,
                "stream key not initialized");

            List<MapRecord<String, String, String>> records = RedisStreamUtils.readEvents(
                redisTemplate,
                currentStreamKey,
                currentLastId,
                Math.max(getBlockTimeoutMs(), 0),
                (long) Math.max(1, getPollSize())
            );

            if (records == null || records.isEmpty()) {
                return;
            }

            for (MapRecord<String, String, String> record : records) {
                try {
                    Map<String, String> payload = Objects.requireNonNull(record.getValue(),
                        logPrefix + " payload is null");
                    handleRecord(payload);
                    // 마지막 읽은 ID 업데이트 (다음 읽기 시 이 ID 이후부터 읽음)
                    lastReadId.set(record.getId().getValue());
                } catch (Exception recordError) {
                    log.warn("[{}] 레코드 {} 처리 실패: {}",
                        logPrefix,
                        record.getId(),
                        recordError.getMessage(),
                        recordError);
                    // 처리 실패해도 ID는 업데이트하여 다음 레코드로 진행
                    lastReadId.set(record.getId().getValue());
                }
            }
        } catch (Exception e) {
            log.warn("[{}] 스트림 소비 실패: {}", logPrefix, e.getMessage(), e);
        }
    }

    protected abstract void handleRecord(Map<String, String> payload);

    protected abstract int getPollSize();

    protected abstract long getBlockTimeoutMs();
}
