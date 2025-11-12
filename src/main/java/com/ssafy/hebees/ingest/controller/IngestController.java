package com.ssafy.hebees.ingest.controller;


import com.ssafy.hebees.common.dto.PageRequest;
import com.ssafy.hebees.common.dto.PageResponse;
import com.ssafy.hebees.common.response.BaseResponse;
import com.ssafy.hebees.common.util.SecurityUtil;
import com.ssafy.hebees.ingest.dto.response.IngestProgressMetaWithStepsResponse;
// import removed: IngestProgressSummaryPageResponse
import com.ssafy.hebees.ingest.dto.response.IngestProgressSummaryListResponse;
import com.ssafy.hebees.ingest.dto.response.IngestProgressEventResponse;
import com.ssafy.hebees.ingest.dto.response.IngestProgressSummaryResponse;
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
        PageRequest pageRequest
    ) {
        var userUuid = SecurityUtil.getCurrentUserUuid()
            .orElseThrow(() -> new RuntimeException("인증된 사용자 없음"));
        IngestProgressSummaryListResponse result =
            progressService.getRunningMetaWithStepsPageForUserWithSummary(userUuid, pageRequest);
        return ResponseEntity.ok(BaseResponse.success(result));
    }

    // 진행 상황 SSE 스트리밍 (초기 스냅샷 + 실시간 업데이트)
    @GetMapping(value = "/progress/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    @Operation(summary = "진행 상황 SSE 스트리밍", description = "초기 상태를 보낸 뒤 Redis Stream 기반 실시간 업데이트를 전송합니다.")
    public SseEmitter streamMyRunProgress() {
        var userUuid = SecurityUtil.getCurrentUserUuid()
            .orElseThrow(() -> new RuntimeException("인증된 사용자 없음"));

        // runId 및 meta 조회 후 초기 이벤트 구성
        String runId = progressService.getActiveRunId(userUuid);
        java.util.Map<Object, Object> meta = progressService.getMeta(runId);
        IngestProgressEventResponse initial = IngestProgressEventResponse.fromMaps(
            meta,
            java.util.Map.of(),
            userUuid,
            "META_SNAPSHOT"
        );
        String lastId = "$"; // 새 이벤트부터 수신

        // 무제한 타임아웃(프록시 환경에 따라 조정 가능)
        SseEmitter emitter = new SseEmitter(0L);

        java.util.concurrent.ExecutorService executor = java.util.concurrent.Executors.newSingleThreadExecutor(
            r -> {
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
            IngestProgressSummaryResponse summary = progressService.getSummaryForUser(userUuid);
            emitter.send(SseEmitter.event().name("summary").data(summary));
            emitter.send(SseEmitter.event().name("initial").data(initial));
        } catch (Exception e) {
            emitter.completeWithError(e);
            return emitter;
        }

        final String initialLastId = lastId;
        executor.submit(() -> {
            // lastId/runId는 위에서 계산됨
            java.util.concurrent.atomic.AtomicReference<String> lastRef = new java.util.concurrent.atomic.AtomicReference<>(
                initialLastId);
            boolean done = false;
            while (!done && !Thread.currentThread().isInterrupted()) {
                try {
                    var records = progressService.readEvents(runId, lastRef.get(), 10000L, 10L);
                    if (records != null && !records.isEmpty()) {
                        for (var rec : records) {
                            var dto = progressService.toEventFromRecord(userUuid, runId, meta, rec);
                            lastRef.set(rec.getId().getValue());
                            try {
                                emitter.send(SseEmitter.event().name("progress").data(dto));
                            } catch (Exception sendEx) {
                                emitter.completeWithError(sendEx);
                                done = true;
                                break;
                            }
                            String status = dto.status();
                            if (status != null && ("COMPLETED".equalsIgnoreCase(status)
                                || "FAILED".equalsIgnoreCase(status)
                                || "completed".equalsIgnoreCase(status)
                                || "failed".equalsIgnoreCase(status))) {
                                // 종료 직전 summary 갱신 전송
                                try {
                                    IngestProgressSummaryResponse summary = progressService.getSummaryForUser(
                                        userUuid);
                                    emitter.send(SseEmitter.event().name("summary").data(summary));
                                } catch (Exception sendEx) {
                                    emitter.completeWithError(sendEx);
                                    done = true;
                                    break;
                                }
                                done = true;
                                break;
                            }
                        }
                    } else {
                        // 주기적 heartbeat
                        try {
                            emitter.send(SseEmitter.event().name("heartbeat").data("keepalive"));
                        } catch (Exception ignore) { /* ignore send failure here */ }
                    }
                } catch (Exception e) {
                    // 읽기 오류가 지속되면 종료
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
    public ResponseEntity<BaseResponse<java.util.Map<String, Object>>> pushTestEvents(
        @RequestParam(name = "delayMs", required = false, defaultValue = "0") Long delayMs
    ) {
        var userUuid = SecurityUtil.getCurrentUserUuid()
            .orElseThrow(() -> new RuntimeException("인증된 사용자 없음"));

        var ids = progressService.pushTestSequence(userUuid, delayMs);
        java.util.Map<String, Object> result = new java.util.HashMap<>();
        result.put("count", ids.size());
        result.put("ids", ids);
        return ResponseEntity.ok(BaseResponse.success(result));
    }
}
