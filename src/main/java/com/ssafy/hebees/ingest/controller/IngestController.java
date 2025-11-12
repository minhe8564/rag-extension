package com.ssafy.hebees.ingest.controller;

import com.ssafy.hebees.common.dto.PageRequest;
import com.ssafy.hebees.common.response.BaseResponse;
import com.ssafy.hebees.common.util.SecurityUtil;
import com.ssafy.hebees.ingest.dto.response.IngestProgressEventResponse;
import com.ssafy.hebees.ingest.dto.response.IngestProgressSummaryListResponse;
import com.ssafy.hebees.ingest.service.IngestRunProgressService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;
import jakarta.servlet.http.HttpServletRequest;

import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicReference;

@Slf4j
@RestController
@RequestMapping("/ingest/")
@RequiredArgsConstructor
@Tag(name = "Ingest", description = "문서 수집 진행 상태 API")
public class IngestController {

    private final IngestRunProgressService progressService;

    // 진행 상황 조회 (JWT 사용자 기반)
    @GetMapping("/progress")
    @Operation(summary = "진행 상황 조회", description = "진행 중(RUNNING) 메타 + 단계별 퍼센티지를 페이지네이션하여 반환")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "조회 성공"),
        @ApiResponse(responseCode = "401", description = "인증 필요"),
        @ApiResponse(responseCode = "404", description = "진행 중인 run 없음")
    })
    public ResponseEntity<BaseResponse<IngestProgressSummaryListResponse>> getMyRunProgress(
        PageRequest pageRequest) {
        var userUuid = SecurityUtil.getCurrentUserUuid()
            .orElseThrow(() -> new RuntimeException("인증된 사용자 없음"));
        IngestProgressSummaryListResponse result = progressService
            .getRunningMetaWithStepsPageForUserWithSummary(userUuid, pageRequest);
        return ResponseEntity.ok(BaseResponse.success(result));
    }

    // 진행 상황 SSE 스트리밍 (초기 스냅샷 + 실시간 업데이트)
    @GetMapping(value = "/progress/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter streamMyRunProgress(HttpServletRequest req) {
        var userUuid = SecurityUtil.getCurrentUserUuid()
            .orElseThrow(() -> new RuntimeException("인증된 사용자 없음"));

        String runId = progressService.getActiveRunId(userUuid);
        if (runId == null) { // 활성 run 없을 때도 스트림 열어 두기
            runId = "";
        }
        Map<Object, Object> meta = runId.isEmpty() ? Map.of() : progressService.getMeta(runId);

        IngestProgressEventResponse initial = IngestProgressEventResponse.fromMaps(
            meta, Map.of(), userUuid, "META_SNAPSHOT");

        // 1) Last-Event-ID 우선, 없으면 "0-0"
        String lastIdHdr = req.getHeader("Last-Event-ID");
        String lastId = (lastIdHdr != null && !lastIdHdr.isBlank()) ? lastIdHdr : "0-0";

        SseEmitter emitter = new SseEmitter(0L);
        ExecutorService executor = Executors.newSingleThreadExecutor(r -> {
            Thread t = new Thread(r, "ingest-sse-" + userUuid);
            t.setDaemon(true);
            return t;
        });

        emitter.onCompletion(executor::shutdown);
        emitter.onTimeout(() -> {
            try {
                emitter.complete();
            } finally {
                executor.shutdownNow();
            }
        });
        emitter.onError(e -> {
            try {
                emitter.completeWithError(e);
            } finally {
                executor.shutdownNow();
            }
        });

        try {
            // 2) 초기 스냅샷에도 id를 넣어두면 클라가 일관되게 처리 가능
            emitter.send(SseEmitter.event().name("initial").id(lastId).data(initial));
        } catch (Exception e) {
            emitter.completeWithError(e);
            return emitter;
        }

        final String initialRunId = runId;
        final String initialLastId = lastId;

        executor.submit(() -> {
            log.info("[INGEST] SSE 스트림 루프 시작 - userUuid={}, initialRunId={}", userUuid,
                initialRunId);
            AtomicReference<String> currentRunIdRef = new AtomicReference<>(initialRunId);
            AtomicReference<Map<Object, Object>> currentMetaRef = new AtomicReference<>(meta);
            AtomicReference<String> lastRef = new AtomicReference<>(initialLastId);
            boolean done = false;
            int loopCount = 0;

            while (!done && !Thread.currentThread().isInterrupted()) {
                try {
                    loopCount++;
                    if (loopCount % 10 == 0) {
                        log.info("[INGEST] SSE 루프 실행 중 - loopCount={}, currentRunId={}", loopCount,
                            currentRunIdRef.get());
                    }

                    // 3) 새 run 감지: 매 루프마다 확인 (블로킹 전에 확인)
                    String newRunId = null;
                    try {
                        log.debug("[INGEST] 활성 runId 조회 시도 - userUuid={}", userUuid);
                        newRunId = progressService.getActiveRunId(userUuid);
                        log.debug("[INGEST] 활성 runId 조회 결과 - newRunId={}", newRunId);
                    } catch (Exception e) {
                        // 활성 run이 없으면 null로 유지
                        log.warn("[INGEST] 활성 runId 조회 실패 - userUuid={}, error={}", userUuid,
                            e.getMessage());
                    }

                    String currentRunId = currentRunIdRef.get();
                    log.debug("[INGEST] runId 비교 - currentRunId={}, newRunId={}", currentRunId,
                        newRunId);

                    if (newRunId != null && !newRunId.equals(currentRunId)) {
                        log.info("[INGEST] 새로운 runId 감지: {} -> {}", currentRunId, newRunId);
                        currentRunIdRef.set(newRunId);
                        Map<Object, Object> newMeta = progressService.getMeta(newRunId);
                        currentMetaRef.set(newMeta);

                        IngestProgressEventResponse newInitial = IngestProgressEventResponse.fromMaps(
                            newMeta, Map.of(), userUuid, "META_SNAPSHOT");

                        // 4) 전환 시 lastRef는 "0-0"으로 설정 (stream의 시작부터 모든 메시지 읽기)
                        // "0-0"은 stream의 첫 번째 메시지부터 읽기 시작 (ReadOffset.from("0-0") 사용)
                        lastRef.set("0-0");
                        try {
                            emitter.send(
                                SseEmitter.event().name("initial").id("0-0").data(newInitial));
                        } catch (Exception sendEx) {
                            log.error("[INGEST] 새 run 초기 이벤트 전송 실패", sendEx);
                            emitter.completeWithError(sendEx);
                            done = true;
                            break;
                        }

                        currentRunId = newRunId;
                    }

                    if (currentRunId == null || currentRunId.isBlank()) {
                        // 활성 run이 아직 없다면 하트비트
                        log.debug("[INGEST] 활성 run 없음 - heartbeat 전송");
                        try {
                            emitter.send(SseEmitter.event().comment("keepalive"));
                        } catch (Exception ignore) {
                            /* ignore send failure here */
                        }
                        Thread.sleep(2000);
                        continue;
                    }

                    // 블로킹 시간을 2초로 줄여서 새로운 runId를 더 자주 확인할 수 있도록 함
                    String lastIdToRead = lastRef.get();
                    log.debug("[INGEST] 이벤트 읽기 시도 - runId={}, lastId={}", currentRunId,
                        lastIdToRead);
                    var records = progressService.readEvents(currentRunId, lastIdToRead, 2000L,
                        10L);
                    log.debug("[INGEST] 이벤트 읽기 결과 - runId={}, recordsCount={}", currentRunId,
                        records != null ? records.size() : 0);
                    if (records != null && !records.isEmpty()) {
                        log.debug("[INGEST] {}개의 이벤트 수신 - runId={}", records.size(), currentRunId);
                        for (var rec : records) {
                            var dto = progressService.toEventFromRecord(
                                userUuid, currentRunId, currentMetaRef.get(), rec);

                            String rid = rec.getId().getValue();
                            lastRef.set(rid);

                            // 5) progress에도 반드시 id 포함
                            try {
                                emitter.send(SseEmitter.event().name("progress").id(rid).data(dto));
                                log.debug(
                                    "[INGEST] progress 이벤트 전송 - runId={}, eventId={}, status={}",
                                    currentRunId, rid, dto.status());
                            } catch (Exception sendEx) {
                                log.error("[INGEST] progress 이벤트 전송 실패", sendEx);
                                emitter.completeWithError(sendEx);
                                done = true;
                                break;
                            }

                            String status = dto.status();
                            if (status != null && ("COMPLETED".equalsIgnoreCase(status)
                                || "FAILED".equalsIgnoreCase(status))) {
                                // 여기서 바로 done=true로 끝내지 말고, 다음 루프에서 새 run 감지
                                log.info("[INGEST] 현재 run 완료 - runId={}, status={}", currentRunId,
                                    status);
                            }
                        }
                    } else {
                        // 이벤트가 없을 때 heartbeat
                        log.debug("[INGEST] 이벤트 없음 - heartbeat 전송 - runId={}", currentRunId);
                        try {
                            emitter.send(SseEmitter.event().comment("keepalive"));
                        } catch (Exception ignore) {
                            /* ignore send failure here */
                        }
                        // 짧은 대기 후 다음 루프로 (새 runId 감지 기회 제공)
                        Thread.sleep(500);
                    }
                } catch (Exception e) {
                    log.error("[INGEST] SSE 스트림 처리 중 오류 발생", e);
                    try {
                        emitter.completeWithError(e);
                    } catch (Exception ignored) {
                    }
                    done = true;
                }
            }
            try {
                emitter.complete();
            } catch (Exception ignored) {
            }
        });

        return emitter;
    }

    // 테스트용: 현재 사용자 활성 run에 진행 이벤트(EXTRACTION -> EMBEDDING -> VECTOR_STORE) 푸시
    @PostMapping("/progress/test/push")
    @Operation(summary = "SSE 테스트 이벤트 푸시", description = "현재 사용자 활성 run에 테스트 진행 이벤트 3건을 순차 푸시합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "푸시 성공"),
        @ApiResponse(responseCode = "401", description = "인증 필요"),
        @ApiResponse(responseCode = "404", description = "활성 run 없음")
    })
    public ResponseEntity<BaseResponse<Map<String, Object>>> pushTestEvents(
        @RequestParam(name = "delayMs", required = false, defaultValue = "0") Long delayMs) {
        var userUuid = SecurityUtil.getCurrentUserUuid()
            .orElseThrow(() -> new RuntimeException("인증된 사용자 없음"));

        var ids = progressService.pushTestSequence(userUuid, delayMs);
        Map<String, Object> result = new HashMap<>();
        result.put("count", ids.size());
        result.put("ids", ids);
        return ResponseEntity.ok(BaseResponse.success(result));
    }
}
