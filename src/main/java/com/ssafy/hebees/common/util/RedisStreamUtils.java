package com.ssafy.hebees.common.util;

import java.util.Map;
import lombok.NoArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Range;
import org.springframework.data.redis.connection.stream.MapRecord;
import org.springframework.data.redis.connection.stream.ReadOffset;
import org.springframework.data.redis.connection.stream.StreamOffset;
import org.springframework.data.redis.connection.stream.StreamReadOptions;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.data.redis.core.StreamOperations;

import java.time.Duration;
import java.util.Collections;
import java.util.List;

/**
 * Redis Stream 공통 유틸리티
 */
@Slf4j
@NoArgsConstructor
public class RedisStreamUtils {

    /**
     * Redis Stream에서 이벤트를 블로킹으로 읽어옵니다.
     *
     * @param redisTemplate Redis 템플릿
     * @param streamKey     Stream 키
     * @param lastId        마지막 읽은 ID (null/"$"인 경우 최신 이후의 신규 메시지만 읽기)
     * @param blockMillis   블로킹 대기 시간 (밀리초, 0이면 non-blocking)
     * @param count         최대 읽을 레코드 수 (null이면 제한 없음)
     * @param <K>           키 타입
     * @param <HK>          해시 키 타입
     * @param <HV>          해시 값 타입
     * @return 읽은 레코드 목록
     */
    @SuppressWarnings("unchecked")
    public static <K, HK, HV> List<MapRecord<K, HK, HV>> readEvents(
        RedisTemplate<K, ?> redisTemplate,
        K streamKey,
        String lastId,
        long blockMillis,
        Long count) {
        StreamOperations<K, ?, ?> streamOps = redisTemplate.opsForStream();
        StreamReadOptions options = StreamReadOptions.empty();
        if (blockMillis > 0) {
            options = options.block(Duration.ofMillis(blockMillis));
        }
        if (count != null && count > 0) {
            options = options.count(count);
        }
        ReadOffset offset;
        if (lastId == null || lastId.isBlank() || "$".equals(lastId)) {
            // 최신 이후의 신규 메시지만 읽기
            offset = ReadOffset.latest();
        } else {
            // lastId 이후의 메시지 읽기 (exclusive)
            offset = ReadOffset.from(lastId);
        }
        try {
            List<? extends MapRecord<K, ?, ?>> result = streamOps.read(
                options, StreamOffset.create(streamKey, offset));
            return result != null ? (List<MapRecord<K, HK, HV>>) (List<?>) result
                : Collections.emptyList();
        } catch (Exception e) {
            log.warn("Stream 읽기 실패 - streamKey={}, lastId={}, err={}", streamKey, lastId,
                e.toString());
            return Collections.emptyList();
        }
    }

    /**
     * Redis Stream에 레코드를 추가합니다.
     *
     * @param redisTemplate Redis 템플릿
     * @param streamKey     Stream 키
     * @param record        추가할 레코드 (Map 형태)
     * @param <K>           키 타입
     * @param <HK>          해시 키 타입
     * @param <HV>          해시 값 타입
     * @return 추가된 레코드의 ID
     */
    public static <K, HK, HV> String addRecord(
        RedisTemplate<K, HV> redisTemplate,
        K streamKey,
        Map<HK, HV> record) {
        StreamOperations<K, HK, HV> streamOps = redisTemplate.opsForStream();
        try {
            return streamOps.add(streamKey, record).getValue();
        } catch (Exception e) {
            log.error("Stream 레코드 추가 실패 - streamKey={}, err={}", streamKey, e.toString());
            throw new RuntimeException("Failed to add record to stream", e);
        }
    }

    /**
     * Redis Stream의 크기를 제한합니다 (최근 N개만 유지).
     *
     * @param redisTemplate Redis 템플릿
     * @param streamKey     Stream 키
     * @param maxLength     최대 유지할 레코드 수
     * @param approximate   근사치 사용 여부 (true면 성능 향상, false면 정확한 크기)
     * @param <K>           키 타입
     * @param <HV>          해시 값 타입
     * @return 제거된 레코드 수
     */
    public static <K, HV> Long trimStream(
        RedisTemplate<K, HV> redisTemplate,
        K streamKey,
        long maxLength,
        boolean approximate) {
        StreamOperations<K, ?, ?> streamOps = redisTemplate.opsForStream();
        try {
            return streamOps.trim(streamKey, maxLength, approximate);
        } catch (Exception e) {
            log.warn("Stream trim 실패 - streamKey={}, maxLength={}, err={}", streamKey, maxLength,
                e.toString());
            return 0L;
        }
    }

    /**
     * Redis Stream에서 최신 레코드를 조회합니다 (역순).
     *
     * @param redisTemplate Redis 템플릿
     * @param streamKey     Stream 키
     * @param limit         최대 조회할 레코드 수 (null이면 제한 없음)
     * @param <K>           키 타입
     * @param <HK>          해시 키 타입
     * @param <HV>          해시 값 타입
     * @return 최신 레코드 목록 (최신순)
     */
    @SuppressWarnings("unchecked")
    public static <K, HK, HV> List<MapRecord<K, HK, HV>> getLatestRecords(
        RedisTemplate<K, ?> redisTemplate,
        K streamKey,
        Long limit) {
        StreamOperations<K, ?, ?> streamOps = redisTemplate.opsForStream();
        try {
            Range<String> range = org.springframework.data.domain.Range.unbounded();
            List<? extends MapRecord<K, ?, ?>> records = streamOps.reverseRange(streamKey, range);
            if (records != null && !records.isEmpty() && limit != null && limit > 0) {
                List<MapRecord<K, HK, HV>> result = new java.util.ArrayList<>();
                int maxIndex = Math.min(records.size(), limit.intValue());
                for (int i = 0; i < maxIndex; i++) {
                    result.add((MapRecord<K, HK, HV>) records.get(i));
                }
                return result;
            }
            return records != null ? (List<MapRecord<K, HK, HV>>) (List<?>) records
                : Collections.emptyList();
        } catch (Exception e) {
            log.warn("Stream 최신 레코드 조회 실패 - streamKey={}, limit={}, err={}", streamKey, limit,
                e.toString());
            return Collections.emptyList();
        }
    }

    /**
     * Redis Stream에서 최신 레코드의 ID를 조회합니다.
     *
     * @param redisTemplate Redis 템플릿
     * @param streamKey     Stream 키
     * @param <K>           키 타입
     * @return 최신 레코드의 ID (없으면 null)
     */
    public static <K> String getLatestRecordId(
        RedisTemplate<K, ?> redisTemplate,
        K streamKey) {
        List<? extends MapRecord<?, ?, ?>> records = getLatestRecords(redisTemplate, streamKey, 1L);
        if (records != null && !records.isEmpty()) {
            return records.get(0).getId().getValue();
        }
        return null;
    }
}

