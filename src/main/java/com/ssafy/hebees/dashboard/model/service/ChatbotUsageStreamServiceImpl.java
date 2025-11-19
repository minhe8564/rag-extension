package com.ssafy.hebees.dashboard.model.service;

import com.ssafy.hebees.common.util.MonitoringUtils;
import com.ssafy.hebees.dashboard.dto.response.ChatbotRequestCountResponse;
import java.io.IOException;
import java.time.Duration;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.CopyOnWriteArraySet;
import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.atomic.AtomicReference;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

@Slf4j
@Service
//@RequiredArgsConstructor
public class ChatbotUsageStreamServiceImpl implements ChatbotUsageStreamService {

    private static final long BUCKET_SECONDS = 10L;
    private static final long BUCKET_MILLIS = BUCKET_SECONDS * 1000L;
    private static final Duration KEY_TTL = Duration.ofMinutes(5);
    private static final String CHATBOT_REQUEST_KEY_PREFIX = "metrics:chatbot:requests:";
    private static final ZoneId ZONE_ID = MonitoringUtils.KST;

    private final StringRedisTemplate redisTemplate;
    private final Set<SseEmitter> subscribers = new CopyOnWriteArraySet<>();
    private final AtomicReference<ChatbotRequestCountResponse> lastSnapshot =
        new AtomicReference<>(new ChatbotRequestCountResponse(
            LocalDateTime.now(ZONE_ID).withNano(0),
            0
        ));
    private final AtomicLong lastProcessedBucket = new AtomicLong(-1L);

    public ChatbotUsageStreamServiceImpl(
        @Qualifier("dashboardRedisTemplate") StringRedisTemplate redisTemplate) {
        this.redisTemplate = redisTemplate;
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
        sendEvent(emitter, snapshot, "init", snapshot.timestamp());

        if (StringUtils.hasText(lastEventId)) {
            log.debug("Chatbot stream subscription resumed from event {}", lastEventId);
        }

        return emitter;
    }

    @Scheduled(initialDelay = BUCKET_MILLIS, fixedRate = BUCKET_MILLIS)
    void publishSnapshot() {
        long nowEpoch = Instant.now().getEpochSecond();
        long currentBucketStart = (nowEpoch / BUCKET_SECONDS) * BUCKET_SECONDS;
        long latestProcessableStart = currentBucketStart - BUCKET_SECONDS;

        if (latestProcessableStart < 0) {
            return;
        }

        long previousProcessed = lastProcessedBucket.get();
        if (previousProcessed < 0) {
            previousProcessed = latestProcessableStart - BUCKET_SECONDS;
        }

        long nextBucketStart = previousProcessed + BUCKET_SECONDS;
        boolean processedAny = false;
        while (nextBucketStart <= latestProcessableStart) {
            ChatbotRequestCountResponse snapshot = processBucket(nextBucketStart);
            lastSnapshot.set(snapshot);
            broadcast(snapshot);
            lastProcessedBucket.set(nextBucketStart);
            processedAny = true;
            nextBucketStart += BUCKET_SECONDS;
        }

        if (!processedAny && log.isTraceEnabled()) {
            log.trace("No chatbot metric buckets ready to process (latestProcessableStart={})",
                latestProcessableStart);
        }
    }

    private ChatbotRequestCountResponse processBucket(long bucketStart) {
        String key = buildBucketKey(bucketStart);
        long count = extractAndDeleteCount(key);
        LocalDateTime timestamp = LocalDateTime.ofInstant(
            Instant.ofEpochSecond(bucketStart + BUCKET_SECONDS),
            ZONE_ID
        );
        return new ChatbotRequestCountResponse(timestamp, safeToInt(count));
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
        LocalDateTime timestamp = LocalDateTime.ofInstant(
            Instant.ofEpochSecond(bucketStart + BUCKET_SECONDS),
            ZONE_ID
        );
        ChatbotRequestCountResponse snapshot = new ChatbotRequestCountResponse(
            timestamp, safeToInt(count));
        lastSnapshot.set(snapshot);
        broadcast(snapshot);
    }

    private void broadcast(ChatbotRequestCountResponse snapshot) {
        if (subscribers.isEmpty()) {
            return;
        }

        String eventId = snapshot.timestamp() != null
            ? snapshot.timestamp().toString()
            : Long.toString(System.currentTimeMillis());

        for (SseEmitter emitter : subscribers) {
            sendEvent(emitter, snapshot, "update", eventId);
        }
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
        return (epochSeconds / BUCKET_SECONDS) * BUCKET_SECONDS;
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
}

