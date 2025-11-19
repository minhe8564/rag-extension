package com.ssafy.hebees.dashboard.model.service;

import com.ssafy.hebees.common.util.MonitoringUtils;
import com.ssafy.hebees.dashboard.dto.request.ChatbotRandomConfigRequest;
import com.ssafy.hebees.dashboard.dto.request.ChatbotScheduleConfigRequest;
import com.ssafy.hebees.dashboard.dto.response.ChatbotRandomConfigResponse;
import com.ssafy.hebees.dashboard.dto.response.ChatbotRequestCountResponse;
import com.ssafy.hebees.dashboard.dto.response.ChatbotScheduleConfigResponse;
import jakarta.annotation.PostConstruct;
import java.io.IOException;
import java.time.Duration;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.util.Random;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.CopyOnWriteArraySet;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.atomic.AtomicReference;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.scheduling.TaskScheduler;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

@Slf4j
@Service
//@RequiredArgsConstructor
public class ChatbotUsageStreamServiceImpl implements ChatbotUsageStreamService {

    private static final long DEFAULT_BUCKET_SECONDS = 10L;
    private static final Duration KEY_TTL = Duration.ofMinutes(5);
    private static final String CHATBOT_REQUEST_KEY_PREFIX = "metrics:chatbot:requests:";
    private static final ZoneId ZONE_ID = MonitoringUtils.KST;

    private final StringRedisTemplate redisTemplate;
    private final TaskScheduler taskScheduler;
    private final Set<SseEmitter> subscribers = new CopyOnWriteArraySet<>();
    private final AtomicReference<ChatbotRequestCountResponse> lastSnapshot =
        new AtomicReference<>(new ChatbotRequestCountResponse(
            LocalDateTime.now(ZONE_ID).withNano(0),
            0
        ));
    private final AtomicLong lastProcessedBucket = new AtomicLong(-1L);
    private final AtomicReference<RandomConfig> randomConfig = new AtomicReference<>(
        new RandomConfig(false, 0, 100));
    private final AtomicReference<Long> bucketSeconds = new AtomicReference<>(
        DEFAULT_BUCKET_SECONDS);
    private final AtomicReference<ScheduledFuture<?>> scheduledTask = new AtomicReference<>();
    private final Random random = new Random();

    public ChatbotUsageStreamServiceImpl(
        @Qualifier("dashboardRedisTemplate") StringRedisTemplate redisTemplate,
        TaskScheduler taskScheduler) {
        this.redisTemplate = redisTemplate;
        this.taskScheduler = taskScheduler;
    }

    @PostConstruct
    void initialize() {
        startScheduledTask(bucketSeconds.get());
    }

    @Override
    public void recordChatbotRequest(UUID userNo, UUID sessionNo) {
        long bucketStart = incrementBucket(1L, sessionNo, userNo);
        if (bucketStart >= 0) {
            // 현재 버킷의 값을 즉시 조회하여 SSE 구독자에게 전송
            broadcastCurrentBucket(bucketStart);
        }
    }

    @Override
    public void recordChatbotRequests(long amount) {
        long bucketStart = incrementBucket(amount, null, null);
        if (bucketStart >= 0) {
            // 현재 버킷의 값을 즉시 조회하여 SSE 구독자에게 전송
            broadcastCurrentBucket(bucketStart);
        }
    }

    @Override
    public SseEmitter subscribeChatbotStream(String lastEventId) {
        SseEmitter emitter = new SseEmitter(0L);
        subscribers.add(emitter);

        emitter.onCompletion(() -> removeSubscriber(emitter));
        emitter.onTimeout(() -> removeSubscriber(emitter));
        emitter.onError(throwable -> removeSubscriber(emitter));

        ChatbotRequestCountResponse snapshot = lastSnapshot.get();
        ChatbotRequestCountResponse snapshotWithRandom = addRandomValueIfEnabled(snapshot);
        sendEvent(emitter, snapshotWithRandom, "init", snapshot.timestamp());

        if (StringUtils.hasText(lastEventId)) {
            log.debug("Chatbot stream subscription resumed from event {}", lastEventId);
        }

        return emitter;
    }

    @Override
    public ChatbotRandomConfigResponse setRandomConfig(ChatbotRandomConfigRequest request) {
        RandomConfig config = new RandomConfig(
            request.enabled() != null ? request.enabled() : false,
            request.lower() != null ? request.lower() : 0,
            request.upper() != null ? request.upper() : 100
        );

        // 유효성 검증
        if (config.lower > config.upper) {
            log.warn("Invalid random config: lower={} > upper={}, swapping values",
                config.lower, config.upper);
            int temp = config.lower;
            config.lower = config.upper;
            config.upper = temp;
        }

        randomConfig.set(config);
        log.info("Chatbot random config updated: enabled={}, lower={}, upper={}",
            config.enabled, config.lower, config.upper);

        return new ChatbotRandomConfigResponse(config.enabled, config.lower, config.upper);
    }

    @Override
    public ChatbotRandomConfigResponse getRandomConfig() {
        RandomConfig config = randomConfig.get();
        return new ChatbotRandomConfigResponse(config.enabled, config.lower, config.upper);
    }

    @Override
    public ChatbotScheduleConfigResponse setScheduleConfig(ChatbotScheduleConfigRequest request) {
        long newIntervalSeconds = request.intervalSeconds();
        if (newIntervalSeconds < 1) {
            throw new IllegalArgumentException("intervalSeconds는 1 이상이어야 합니다");
        }

        bucketSeconds.set(newIntervalSeconds);
        startScheduledTask(newIntervalSeconds);

        log.info("Chatbot schedule config updated: intervalSeconds={}", newIntervalSeconds);

        return new ChatbotScheduleConfigResponse((int) newIntervalSeconds);
    }

    @Override
    public ChatbotScheduleConfigResponse getScheduleConfig() {
        return new ChatbotScheduleConfigResponse(bucketSeconds.get().intValue());
    }

    private void startScheduledTask(long intervalSeconds) {
        // 기존 스케줄 취소
        ScheduledFuture<?> existingTask = scheduledTask.getAndSet(null);
        if (existingTask != null) {
            existingTask.cancel(false);
        }

        // 새로운 스케줄 시작
        long intervalMillis = intervalSeconds * 1000L;
        ScheduledFuture<?> newTask = taskScheduler.scheduleAtFixedRate(
            this::publishSnapshot,
            java.time.Instant.now().plusMillis(intervalMillis),
            Duration.ofSeconds(intervalSeconds)
        );
        scheduledTask.set(newTask);

        log.info("Chatbot scheduled task started with interval: {} seconds", intervalSeconds);
    }

    void publishSnapshot() {
        long bucketSecondsValue = bucketSeconds.get();
        long nowEpoch = Instant.now().getEpochSecond();
        long currentBucketStart = (nowEpoch / bucketSecondsValue) * bucketSecondsValue;
        long latestProcessableStart = currentBucketStart - bucketSecondsValue;

        if (latestProcessableStart < 0) {
            return;
        }

        long previousProcessed = lastProcessedBucket.get();
        if (previousProcessed < 0) {
            previousProcessed = latestProcessableStart - bucketSecondsValue;
        }

        long nextBucketStart = previousProcessed + bucketSecondsValue;
        boolean processedAny = false;
        while (nextBucketStart <= latestProcessableStart) {
            ChatbotRequestCountResponse snapshot = processBucket(nextBucketStart);
            lastSnapshot.set(snapshot);
            broadcast(snapshot);
            lastProcessedBucket.set(nextBucketStart);
            processedAny = true;
            nextBucketStart += bucketSecondsValue;
        }

        if (!processedAny && log.isTraceEnabled()) {
            log.trace("No chatbot metric buckets ready to process (latestProcessableStart={})",
                latestProcessableStart);
        }
    }

    private ChatbotRequestCountResponse processBucket(long bucketStart) {
        String key = buildBucketKey(bucketStart);
        long count = extractAndDeleteCount(key);
        long bucketSecondsValue = bucketSeconds.get();
        LocalDateTime timestamp = LocalDateTime.ofInstant(
            Instant.ofEpochSecond(bucketStart + bucketSecondsValue),
            ZONE_ID
        );
        ChatbotRequestCountResponse snapshot = new ChatbotRequestCountResponse(timestamp,
            safeToInt(count));
        return addRandomValueIfEnabled(snapshot);
    }

    private long extractAndDeleteCount(String key) {
        try {
            String raw = redisTemplate.opsForValue().get(key);
            long count = 0L;
            if (raw != null) {
                try {
                    count = Long.parseLong(raw);
                } catch (NumberFormatException e) {
                    log.warn("Invalid chatbot request count for key {}: {}", key, raw);
                }
            }
            redisTemplate.delete(key);
            return count;
        } catch (Exception e) {
            log.warn("Failed to fetch chatbot request count from Redis key {}: {}", key,
                e.getMessage());
            return 0L;
        }
    }

    private long getCurrentBucketCount(long bucketStart) {
        String key = buildBucketKey(bucketStart);
        try {
            String raw = redisTemplate.opsForValue().get(key);
            if (raw != null) {
                try {
                    return Long.parseLong(raw);
                } catch (NumberFormatException e) {
                    log.warn("Invalid chatbot request count for key {}: {}", key, raw);
                }
            }
            return 0L;
        } catch (Exception e) {
            log.warn("Failed to fetch chatbot request count from Redis key {}: {}", key,
                e.getMessage());
            return 0L;
        }
    }

    private void broadcastCurrentBucket(long bucketStart) {
        if (subscribers.isEmpty()) {
            return;
        }
        long count = getCurrentBucketCount(bucketStart);
        long bucketSecondsValue = bucketSeconds.get();
        LocalDateTime timestamp = LocalDateTime.ofInstant(
            Instant.ofEpochSecond(bucketStart + bucketSecondsValue),
            ZONE_ID
        );
        ChatbotRequestCountResponse snapshot = new ChatbotRequestCountResponse(
            timestamp, safeToInt(count));
        ChatbotRequestCountResponse snapshotWithRandom = addRandomValueIfEnabled(snapshot);
        lastSnapshot.set(snapshotWithRandom);
        broadcast(snapshotWithRandom);
    }

    private void broadcast(ChatbotRequestCountResponse snapshot) {
        if (subscribers.isEmpty()) {
            return;
        }

        String eventId = snapshot.timestamp() != null
            ? snapshot.timestamp().toString()
            : Long.toString(System.currentTimeMillis());

        ChatbotRequestCountResponse snapshotWithRandom = addRandomValueIfEnabled(snapshot);
        for (SseEmitter emitter : subscribers) {
            sendEvent(emitter, snapshotWithRandom, "update", eventId);
        }
    }

    private ChatbotRequestCountResponse addRandomValueIfEnabled(
        ChatbotRequestCountResponse snapshot) {
        RandomConfig config = randomConfig.get();
        if (config.enabled) {
            int randomValue = generateRandomValue(config.lower, config.upper);
            int requestCountWithRandom = snapshot.requestCount() + randomValue;
            return new ChatbotRequestCountResponse(
                snapshot.timestamp(),
                requestCountWithRandom
            );
        }
        return snapshot;
    }

    private int generateRandomValue(int lower, int upper) {
        if (lower > upper) {
            log.warn("Invalid range: lower={}, upper={}, swapping values", lower, upper);
            int temp = lower;
            lower = upper;
            upper = temp;
        }
        if (lower == upper) {
            return lower;
        }
        return random.nextInt(upper - lower + 1) + lower;
    }

    private void sendEvent(SseEmitter emitter, ChatbotRequestCountResponse snapshot,
        String eventName,
        Object eventId) {
        try {
            emitter.send(SseEmitter.event()
                .id(String.valueOf(eventId))
                .name(eventName)
                .data(snapshot));
        } catch (IOException e) {
            log.debug("SSE send failed for chatbot stream: {}", e.getMessage());
            removeSubscriber(emitter);
            emitter.completeWithError(e);
        }
    }

    private void removeSubscriber(SseEmitter emitter) {
        subscribers.remove(emitter);
    }

    private long incrementBucket(long amount, UUID sessionNo, UUID userNo) {
        if (amount <= 0) {
            log.debug("Ignored non-positive chatbot request amount: {}", amount);
            return -1L;
        }

        long bucketStart = currentBucketStart();
        String key = buildBucketKey(bucketStart);
        try {
            redisTemplate.opsForValue().increment(key, amount);
            redisTemplate.expire(key, KEY_TTL);
            return bucketStart;
        } catch (Exception e) {
            log.warn(
                "Failed to record chatbot requests: bucket={}, sessionNo={}, userNo={}, amount={}, reason={}",
                bucketStart, sessionNo, userNo, amount, e.getMessage());
            return -1L;
        }
    }

    private long currentBucketStart() {
        long epochSeconds = Instant.now().getEpochSecond();
        long bucketSecondsValue = bucketSeconds.get();
        return (epochSeconds / bucketSecondsValue) * bucketSecondsValue;
    }

    private String buildBucketKey(long bucketStart) {
        return CHATBOT_REQUEST_KEY_PREFIX + bucketStart;
    }

    private int safeToInt(long value) {
        if (value > Integer.MAX_VALUE) {
            return Integer.MAX_VALUE;
        }
        if (value < Integer.MIN_VALUE) {
            return Integer.MIN_VALUE;
        }
        return (int) value;
    }

    private static class RandomConfig {

        final boolean enabled;
        int lower;
        int upper;

        RandomConfig(boolean enabled, int lower, int upper) {
            this.enabled = enabled;
            this.lower = lower;
            this.upper = upper;
        }
    }
}

