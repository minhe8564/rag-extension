package com.ssafy.hebees.ingest.service;

import com.ssafy.hebees.common.exception.BusinessException;
import com.ssafy.hebees.common.exception.ErrorCode;
import com.ssafy.hebees.ingest.dto.response.*;
// import removed: IngestProgressSummaryPageResponse no longer used
import com.ssafy.hebees.common.dto.PageRequest;
import com.ssafy.hebees.common.dto.PageResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Qualifier;
import com.ssafy.hebees.common.util.RedisStreamUtils;
import com.ssafy.hebees.common.util.RedisIngestUtils;
import org.springframework.data.redis.connection.stream.MapRecord;
import org.springframework.data.redis.core.*;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.HashMap;

@Slf4j
@Service
public class IngestRunProgressService {

    private final StringRedisTemplate ingestRedisTemplate;

    // 명시적 생성자에 @Qualifier 적용 — db1 템플릿 주입 보장
    public IngestRunProgressService(
        @Qualifier("ingestRedisTemplate") StringRedisTemplate ingestRedisTemplate) {
        this.ingestRedisTemplate = ingestRedisTemplate;
    }

    // ===== SSE 전용 보조 메서드 =====

    public String getActiveRunId(java.util.UUID userUuid) {
        return resolveActiveRunId(userUuid);
    }

    public java.util.Map<Object, Object> getMeta(String runId) {
        HashOperations<String, Object, Object> hops = ingestRedisTemplate.opsForHash();
        return hops.entries(RedisIngestUtils.runMetaKey(runId));
    }

    public IngestProgressEventResponse toEventFromRecord(java.util.UUID userUuid,
        String runId,
        java.util.Map<Object, Object> meta,
        org.springframework.data.redis.connection.stream.MapRecord<String, Object, Object> rec) {
        java.util.Map<?, ?> fields = rec.getValue();
        return IngestProgressEventResponse.fromMaps(meta, fields, userUuid, null);
    }

    /**
     * 사용자 실행 목록(Set)과 각 run의 meta 해시를 확인하여 상태가 RUNNING 이고 createdAt이 가장 최신인 runId를 선택합니다.
     */
    private String resolveActiveRunId(java.util.UUID userUuid) {
        String setKey = RedisIngestUtils.userRunsKey(userUuid.toString());
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
            String metaKey = RedisIngestUtils.runMetaKey(runId);
            Object status = hops.get(metaKey, "status");
            Object created = hops.get(metaKey, "createdAt");
            //log.info("[INGEST] 후보 run 검사 - runId={}, status={}, createdAt={}", runId, status,
            //    created);
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
    private String streamKey(String runId) {
        return RedisIngestUtils.runEventsKey(runId);
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

    // ===== 테스트용 이벤트 푸시 유틸 =====

    public String appendEvent(String runId, java.util.Map<String, String> fields) {
        return RedisStreamUtils.addRecord(ingestRedisTemplate, streamKey(runId), fields);
    }

    /**
     * 연결 검증용 간단 시나리오를 푸시합니다. 순서: EXTRACTION(33.3%) -> EMBEDDING(66.6%) -> VECTOR_STORE(100%,
     * COMPLETED) 각 단계 progressPct=100으로 설정하고, delayMs 간격으로 푸시합니다.
     */
    public java.util.List<String> pushTestSequence(java.util.UUID userUuid, Long delayMs) {
        String runId = resolveActiveRunId(userUuid);
        long delay = delayMs == null ? 0L : Math.max(0L, delayMs);

        String[] steps = {"EXTRACTION", "EMBEDDING", "VECTOR_STORE"};
        double[] overall = {33.3, 66.6, 100.0};
        java.util.List<String> ids = new java.util.ArrayList<>(steps.length);

        for (int i = 0; i < steps.length; i++) {
            HashMap<String, String> fields = new HashMap<>();
            fields.put("eventType", "STEP_UPDATE");
            fields.put("step", steps[i]);
            fields.put("status", i < steps.length - 1 ? "RUNNING" : "COMPLETED");
            fields.put("progressPct", "100");
            fields.put("overallPct", Double.toString(overall[i]));
            fields.put("ts", Long.toString(System.currentTimeMillis()));

            String id = appendEvent(runId, fields);
            ids.add(id);

            if (delay > 0 && i < steps.length - 1) {
                try {
                    Thread.sleep(delay);
                } catch (InterruptedException ie) {
                    Thread.currentThread().interrupt();
                    break;
                }
            }
        }
        return ids;
    }

    /**
     * 진행 중(RUNNING) 메타에 대해 각 run의 이벤트 스트림을 조회하여 단계별 퍼센티지를 포함해 반환합니다.
     */
    public PageResponse<IngestProgressMetaWithStepsResponse> getRunningMetaWithStepsPageForUser(
        java.util.UUID userUuid,
        PageRequest pageRequest
    ) {
        String setKey = RedisIngestUtils.userRunsKey(userUuid.toString());
        SetOperations<String, String> sops = ingestRedisTemplate.opsForSet();
        java.util.Set<String> runIds = sops.members(setKey);
        if (runIds == null || runIds.isEmpty()) {
            throw new BusinessException(ErrorCode.NOT_FOUND);
        }

        HashOperations<String, Object, Object> hops = ingestRedisTemplate.opsForHash();
        java.util.List<IngestProgressMetaWithStepsResponse> items = new java.util.ArrayList<>();
        for (String runId : runIds) {
            String metaKey = RedisIngestUtils.runMetaKey(runId);
            java.util.Map<Object, Object> meta = hops.entries(metaKey);
            if (meta == null || meta.isEmpty()) {
                continue;
            }
            Object st = meta.get("status");
            if (st != null && "RUNNING".equalsIgnoreCase(st.toString())) {
                IngestProgressMetaResponse base = IngestProgressMetaResponse.from(meta,
                    java.util.Map.of());
                java.util.List<org.springframework.data.redis.connection.stream.MapRecord<String, Object, Object>> records =
                    com.ssafy.hebees.common.util.RedisStreamUtils.getLatestRecords(
                        ingestRedisTemplate, streamKey(runId), 1000L);
                java.util.List<StepProgressResponse> steps = buildSteps(base, records);
                items.add(IngestProgressMetaWithStepsResponse.of(base, steps));
            }
        }

        if (items.isEmpty()) {
            throw new BusinessException(ErrorCode.NOT_FOUND);
        }

        items.sort((a, b) -> {
            Long at = a.updatedAt() != null ? a.updatedAt() : a.createdAt();
            Long bt = b.updatedAt() != null ? b.updatedAt() : b.createdAt();
            long av = at == null ? 0L : at;
            long bv = bt == null ? 0L : bt;
            return Long.compare(bv, av);
        });

        int pageNum = pageRequest == null ? 0 : pageRequest.pageNum();
        int pageSize = pageRequest == null ? 10 : pageRequest.pageSize();
        long total = items.size();
        int from = Math.min(pageNum * pageSize, (int) total);
        int to = Math.min(from + pageSize, (int) total);
        java.util.List<IngestProgressMetaWithStepsResponse> data = items.subList(from, to);
        return PageResponse.of(data, pageNum, pageSize, total);
    }

    public IngestProgressSummaryListResponse getRunningMetaWithStepsPageForUserWithSummary(
        java.util.UUID userUuid,
        PageRequest pageRequest
    ) {
        String setKey = RedisIngestUtils.userRunsKey(userUuid.toString());
        SetOperations<String, String> sops = ingestRedisTemplate.opsForSet();
        java.util.Set<String> runIds = sops.members(setKey);
        if (runIds == null || runIds.isEmpty()) {
            throw new BusinessException(ErrorCode.NOT_FOUND);
        }

        HashOperations<String, Object, Object> hops = ingestRedisTemplate.opsForHash();

        // Build page items (RUNNING with steps)
        java.util.List<IngestProgressMetaWithStepsResponse> items = new java.util.ArrayList<>();
        // Build summary over ALL runs in set
        int total = 0;
        int completed = 0;

        for (String runId : runIds) {
            String metaKey = RedisIngestUtils.runMetaKey(runId);
            java.util.Map<Object, Object> meta = hops.entries(metaKey);
            if (meta == null || meta.isEmpty()) {
                continue;
            }

            total++;
            Object statusObj = meta.get("status");
            String statusStr = statusObj == null ? null : statusObj.toString();
            if (statusStr != null && "COMPLETED".equalsIgnoreCase(statusStr)) {
                completed++;
            }
            Double overall = safeParseDouble(meta.get("overallPct"));

            // page items: RUNNING only
            if (statusStr != null && "RUNNING".equalsIgnoreCase(statusStr)) {
                IngestProgressMetaResponse base = IngestProgressMetaResponse.from(meta,
                    java.util.Map.of());
                java.util.List<org.springframework.data.redis.connection.stream.MapRecord<String, Object, Object>> records =
                    com.ssafy.hebees.common.util.RedisStreamUtils.getLatestRecords(
                        ingestRedisTemplate, streamKey(runId), 1000L);
                java.util.List<StepProgressResponse> steps = buildSteps(base, records);
                items.add(IngestProgressMetaWithStepsResponse.of(base, steps));
            }
        }

        if (total == 0) {
            throw new BusinessException(ErrorCode.NOT_FOUND);
        }

        IngestProgressSummaryResponse summary = new IngestProgressSummaryResponse(
            completed,
            total
        );

        // sort and paginate items
        items.sort((a, b) -> {
            Long at = a.updatedAt() != null ? a.updatedAt() : a.createdAt();
            Long bt = b.updatedAt() != null ? b.updatedAt() : b.createdAt();
            long av = at == null ? 0L : at;
            long bv = bt == null ? 0L : bt;
            return Long.compare(bv, av);
        });

        int pageNum = pageRequest == null ? 0 : pageRequest.pageNum();
        int pageSize = pageRequest == null ? 10 : pageRequest.pageSize();
        long totalItems = items.size();
        int from = Math.min(pageNum * pageSize, (int) totalItems);
        int to = Math.min(from + pageSize, (int) totalItems);
        java.util.List<IngestProgressMetaWithStepsResponse> data = items.subList(from, to);

        PageResponse<IngestProgressMetaWithStepsResponse> page = PageResponse.of(data, pageNum,
            pageSize, totalItems);
        return new IngestProgressSummaryListResponse(data, summary, page.pagination());
    }

    private static Double safeParseDouble(Object value) {
        try {
            return value == null ? null : Double.parseDouble(value.toString());
        } catch (Exception e) {
            return null;
        }
    }

    private java.util.List<StepProgressResponse> buildSteps(
        IngestProgressMetaResponse base,
        java.util.List<org.springframework.data.redis.connection.stream.MapRecord<String, Object, Object>> records
    ) {
        java.util.Map<String, Double> map = new java.util.HashMap<>();
        // 최신 이벤트부터 스캔하여 각 step의 첫 값만 채택
        if (records != null) {
            for (var rec : records) {
                var fields = rec.getValue();
                Object s = fields.get("currentStep");
                if (s == null) {
                    s = fields.get("step");
                }
                if (s == null) {
                    continue;
                }
                String step = s.toString().toUpperCase();
                if ("VECTOR_STORE".equals(step)) {
                    step = "VECTOR_STORED";
                }
                if (map.containsKey(step)) {
                    continue;
                }
                Double pct = parseDouble(fields.get("progressPct"));
                if (pct == null) {
                    Object st = fields.get("status");
                    if (st != null && "COMPLETED".equalsIgnoreCase(st.toString())) {
                        pct = 100.0;
                    }
                }
                if (pct != null) {
                    map.put(step, pct);
                }
            }
        }
        // 메타의 현재 단계 진행률 보강
        if (base.currentStep() != null && base.progressPct() != null && !map.containsKey(
            base.currentStep())) {
            String step = base.currentStep().toUpperCase();
            if ("VECTOR_STORE".equals(step)) {
                step = "VECTOR_STORED";
            }
            map.put(step, base.progressPct());
        }
        // 고정 순서로 반환
        String[] order = new String[]{"UPLOAD", "EXTRACTION", "EMBEDDING", "VECTOR_STORED"};
        java.util.List<StepProgressResponse> list = new java.util.ArrayList<>(order.length);
        for (String key : order) {
            list.add(new StepProgressResponse(key, map.getOrDefault(key, 0.0)));
        }
        return list;
    }

    private static Double parseDouble(Object value) {
        try {
            return value == null ? null : Double.parseDouble(value.toString());
        } catch (Exception e) {
            return null;
        }
    }
}
