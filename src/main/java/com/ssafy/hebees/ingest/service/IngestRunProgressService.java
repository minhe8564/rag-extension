package com.ssafy.hebees.ingest.service;

import com.ssafy.hebees.common.exception.BusinessException;
import com.ssafy.hebees.common.exception.ErrorCode;
import com.ssafy.hebees.ingest.dto.response.IngestRunProgressResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.data.domain.Range;
import com.ssafy.hebees.common.util.RedisStreamUtils;
import org.springframework.data.redis.connection.stream.MapRecord;
import org.springframework.data.redis.core.*;
import org.springframework.stereotype.Service;

import java.util.List;
import java.time.Duration;

@Slf4j
@Service
public class IngestRunProgressService {

    private final StringRedisTemplate ingestRedisTemplate;

    // 명시적 생성자에 @Qualifier 적용 — db1 템플릿 주입 보장
    public IngestRunProgressService(
        @Qualifier("ingestRedisTemplate") StringRedisTemplate ingestRedisTemplate) {
        this.ingestRedisTemplate = ingestRedisTemplate;
    }

    /**
     * 현재 사용자(UUID)의 진행 중인 최신 수집(run)을 찾아 최신 스냅샷(Hash)과 이벤트 스트림의 마지막 ID를 조합하여 진행 상태를 반환
     */
    public IngestRunProgressResponse getLatestProgressForUser(java.util.UUID userUuid) {
        // 연결된 Redis 정보와 PING 로깅 (DB 인덱스 확인)
        try {
            var cf = ingestRedisTemplate.getConnectionFactory();
            if (cf instanceof org.springframework.data.redis.connection.lettuce.LettuceConnectionFactory lcf) {
                //log.info("[INGEST] Redis DB={} host={} port={}", lcf.getDatabase(), lcf.getHostName(), lcf.getPort());
            }
            String ping = ingestRedisTemplate.execute((RedisCallback<String>) conn -> conn.ping());
            //log.info("[INGEST] PING => {}", ping);
        } catch (Exception e) {
            //log.warn("[INGEST] Redis connectivity check failed: {}", e.getMessage());
        }
        log.info("[INGEST] 진행 상황 조회 시작 - userUuid={}", userUuid);
        String runId = resolveActiveRunId(userUuid);
        log.info("[INGEST] 후보 선정 완료 - runId={}", runId);

        // 문서 정보(meta) 조회
        HashOperations<String, Object, Object> hops = ingestRedisTemplate.opsForHash();
        String metaKey = metaKey(runId);
        Object docId = hops.get(metaKey, "docId");
        Object docName = hops.get(metaKey, "docName");

        // 진행 상태(latest 스냅샷) 조회
        String latestKey = latestKey(runId);
        java.util.Map<Object, Object> latest = hops.entries(latestKey);
        if (latest == null || latest.isEmpty()) {
            log.info("[INGEST] latest 스냅샷 비어있음 - key={}", latestKey);
            // 스냅샷이 없으면 스트림의 마지막 레코드로 대체
            List<MapRecord<String, Object, Object>> records = RedisStreamUtils.getLatestRecords(
                ingestRedisTemplate, streamKey(runId), null);
            int count = (records == null ? 0 : records.size());
            log.info("[INGEST] 스트림 조회 결과 - key={}, count={}", streamKey(runId), count);
            if (records == null || records.isEmpty()) {
                log.warn("[INGEST] 진행률 없음 - userUuid={}, runId={}, snapshot/stream 모두 비어있음",
                    userUuid, runId);
                throw new BusinessException(ErrorCode.NOT_FOUND);
            }
            MapRecord<String, Object, Object> rec = records.get(0);
            java.util.Map<?, ?> f = rec.getValue();
            log.info("[INGEST] 스트림 최신 사용 - id={}, step={}, processed={}, total={}, status={}",
                rec.getId().getValue(), f.get("step"), f.get("processed"), f.get("total"),
                f.get("status"));
            return IngestRunProgressResponse.fromRecordWithMeta(rec, runId, docId, docName);
        }

        // 선택: 마지막 스트림 ID 조회
        String id = null;
        try {
            id = RedisStreamUtils.getLatestRecordId(ingestRedisTemplate, streamKey(runId));
        } catch (Exception ignore) {
        }

        log.info("[INGEST] latest 스냅샷 사용 - key={}, step={}, processed={}, total={}, status={}",
            latestKey, latest.get("step"), latest.get("processed"), latest.get("total"),
            latest.get("status"));
        return IngestRunProgressResponse.fromLatestSnapshot(runId, docId, docName, latest, id);
    }

    /**
     * 사용자 실행 목록(Set)과 각 run의 meta 해시를 확인하여 상태가 RUNNING 이고 createdAt이 가장 최신인 runId를 선택합니다.
     */
    private String resolveActiveRunId(java.util.UUID userUuid) {
        String setKey = userRunsKey(userUuid.toString());
        SetOperations<String, String> sops = ingestRedisTemplate.opsForSet();
        java.util.Set<String> runIds = sops.members(setKey);
        if (runIds == null || runIds.isEmpty()) {
            log.info("[INGEST] 진행 중 runId 없음 - setKey={}", setKey);
            throw new BusinessException(ErrorCode.NOT_FOUND);
        }

        HashOperations<String, Object, Object> hops = ingestRedisTemplate.opsForHash();
        String selected = null;
        long selectedCreatedAt = Long.MIN_VALUE;
        for (String runId : runIds) {
            String metaKey = metaKey(runId);
            Object status = hops.get(metaKey, "status");
            Object created = hops.get(metaKey, "createdAt");
            log.info("[INGEST] 후보 run 검사 - runId={}, status={}, createdAt={}", runId, status,
                created);
            if (status != null && "RUNNING".equalsIgnoreCase(status.toString())) {
                long createdAt = 0L;
                try {
                    if (created != null) {
                        createdAt = Long.parseLong(created.toString());
                    }
                } catch (NumberFormatException ignore) {
                }
                if (createdAt > selectedCreatedAt) {
                    selected = runId;
                    selectedCreatedAt = createdAt;
                }
            }
        }
        if (selected == null) {
            log.info("[INGEST] RUNNING 상태 run 없음 - setKey={} (후보 수: {})", setKey, runIds.size());
            throw new BusinessException(ErrorCode.NOT_FOUND);
        }
        log.info("[INGEST] 최종 선택 runId={}, createdAt={}", selected, selectedCreatedAt);
        return selected;
    }

    // Redis 키 유틸리티
    private String userRunsKey(String userUuid) {
        return "ingest:user:" + userUuid + ":runs";
    }

    private String metaKey(String runId) {
        return "ingest:run:" + runId + ":meta";
    }

    private String latestKey(String runId) {
        return "ingest:run:" + runId + ":latest";
    }

    // parsing helpers removed; using IngestRunProgressResponse factory methods instead

    private String streamKey(String runId) {
        return "ingest:run:" + runId + ":events";
    }

    /**
     * Redis Stream에서 지정한 runId의 이벤트를 블로킹으로 읽어옵니다. lastId 이후의 레코드를 대상으로 하며, null/"$"인 경우 최신 이후의 신규
     * 이벤트만 수신
     */
    public List<MapRecord<String, Object, Object>> readEvents(String runId, String lastId,
        long blockMillis, Long count) {
        return RedisStreamUtils.readEvents(
            ingestRedisTemplate,
            streamKey(runId),
            lastId,
            blockMillis,
            count);
    }
}
