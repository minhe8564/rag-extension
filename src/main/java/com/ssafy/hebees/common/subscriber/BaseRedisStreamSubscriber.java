package com.ssafy.hebees.common.subscriber;

import jakarta.annotation.PostConstruct;
import java.time.Duration;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.UUID;
import lombok.extern.slf4j.Slf4j;
import org.springframework.dao.DataAccessException;
import org.springframework.data.redis.connection.stream.Consumer;
import org.springframework.data.redis.connection.stream.MapRecord;
import org.springframework.data.redis.connection.stream.ReadOffset;
import org.springframework.data.redis.connection.stream.RecordId;
import org.springframework.data.redis.connection.stream.StreamOffset;
import org.springframework.data.redis.connection.stream.StreamReadOptions;
import org.springframework.data.redis.connection.stream.StreamRecords;
import org.springframework.data.redis.core.StreamOperations;
import org.springframework.data.redis.core.StringRedisTemplate;

/**
 * Redis Stream 구독에 필요한 공통 로직을 제공하는 추상 클래스.
 */
@Slf4j
public abstract class BaseRedisStreamSubscriber {

    private final String streamKey;
    private final String groupName;
    private final String logPrefix;
    private final StringRedisTemplate redisTemplate;

    private String consumerName;

    protected BaseRedisStreamSubscriber(
        StringRedisTemplate redisTemplate,
        String streamKey,
        String groupName,
        String logPrefix
    ) {
        this.redisTemplate = Objects.requireNonNull(redisTemplate,
            "redisTemplate must not be null");
        this.streamKey = Objects.requireNonNull(streamKey,
            "streamKey must not be null");
        this.groupName = Objects.requireNonNull(groupName,
            "groupName must not be null");
        this.logPrefix = logPrefix != null ? logPrefix : "STREAM";
    }

    @PostConstruct
    private void initializeSubscriber() {
        consumerName = "consumer-" + UUID.randomUUID();
        ensureConsumerGroup();
    }

    /**
     * 주기적으로 호출되어 Redis Stream에서 메시지를 소비한다.
     */
    protected void pollStreamInternal() {
        StreamOperations<String, String, String> streamOps =
            Objects.requireNonNull(redisTemplate.opsForStream());

        try {
            Duration blockDuration = Duration.ofMillis(Math.max(getBlockTimeoutMs(), 0));
            String consumer = Objects.requireNonNull(consumerName, "consumer name not initialized");
            String currentGroup = Objects.requireNonNull(groupName, "group name not initialized");
            String currentStreamKey = Objects.requireNonNull(streamKey,
                "stream key not initialized");
            List<MapRecord<String, String, String>> records = streamOps.read(
                Consumer.from(currentGroup, consumer),
                StreamReadOptions.empty()
                    .count(Math.max(1, getPollSize()))
                    .block(Objects.requireNonNull(blockDuration)),
                StreamOffset.create(currentStreamKey, ReadOffset.lastConsumed())
            );

            if (records == null || records.isEmpty()) {
                return;
            }

            for (MapRecord<String, String, String> record : records) {
                try {
                    Map<String, String> payload = Objects.requireNonNull(record.getValue(),
                        logPrefix + " payload is null");
                    handleRecord(payload);
                    streamOps.acknowledge(currentStreamKey, currentGroup, record.getId());
                } catch (Exception recordError) {
                    log.warn("[{}] 레코드 {} 처리 실패: {}",
                        logPrefix,
                        record.getId(),
                        recordError.getMessage(),
                        recordError);
                }
            }
        } catch (Exception e) {
            log.warn("[{}] 스트림 소비 실패: {}", logPrefix, e.getMessage(), e);
        }
    }

    protected abstract void handleRecord(Map<String, String> payload);

    protected abstract int getPollSize();

    protected abstract long getBlockTimeoutMs();

    private void ensureConsumerGroup() {
        StreamOperations<String, String, String> streamOps =
            Objects.requireNonNull(redisTemplate.opsForStream());

        String currentStreamKey = Objects.requireNonNull(streamKey, "stream key not initialized");
        String currentGroup = Objects.requireNonNull(groupName, "group name not initialized");

        try {
            streamOps.createGroup(currentStreamKey, ReadOffset.from("0-0"), currentGroup);
            log.info("[{}] Redis 스트림 '{}'에 컨슈머 그룹 '{}'을(를) 생성했습니다.",
                logPrefix, currentStreamKey, currentGroup);
        } catch (DataAccessException e) {
            if (handleCreateGroupException(e, streamOps, currentStreamKey, currentGroup)) {
                return;
            }
            log.warn("[{}] 스트림 '{}'에서 컨슈머 그룹 '{}' 생성 실패: {}",
                logPrefix, currentStreamKey, currentGroup, e.getMessage(), e);
        } catch (Exception e) {
            if (handleCreateGroupException(e, streamOps, currentStreamKey, currentGroup)) {
                return;
            }
            log.warn("[{}] 컨슈머 그룹 '{}' 생성 중 예상치 못한 오류 발생: {}",
                logPrefix, currentGroup, e.getMessage(), e);
        }
    }

    private boolean handleCreateGroupException(Throwable throwable,
        StreamOperations<String, String, String> streamOps,
        String currentStreamKey,
        String currentGroup) {
        String stream = Objects.requireNonNull(currentStreamKey, "stream key must not be null");
        String group = Objects.requireNonNull(currentGroup, "group name must not be null");

        if (messageContains(throwable, "BUSYGROUP")) {
            log.debug("[{}] 컨슈머 그룹 '{}'은(는) 이미 스트림 '{}'에 존재합니다.",
                logPrefix, group, stream);
            return true;
        }
        if (messageContains(throwable, "ERR no such key")) {
            Map<String, String> bootstrapPayload = Map.of("bootstrap", "true");
            RecordId bootstrapId = streamOps.add(StreamRecords
                .newRecord()
                .in(stream)
                .ofMap(Objects.requireNonNull(bootstrapPayload)));
            streamOps.createGroup(stream, ReadOffset.latest(), group);
            streamOps.delete(stream, bootstrapId);
            log.info("[{}] 스트림 '{}' 초기화 후 컨슈머 그룹 '{}' 생성 완료",
                logPrefix, stream, group);
            return true;
        }
        return false;
    }

    private boolean messageContains(Throwable throwable, String token) {
        Throwable current = throwable;
        while (current != null) {
            String message = current.getMessage();
            if (message != null && message.contains(token)) {
                return true;
            }
            current = current.getCause();
        }
        return false;
    }
}
