package com.ssafy.hebees.domain.ingest.controller;

import com.ssafy.hebees.global.response.BaseResponse;
import com.ssafy.hebees.global.util.SecurityUtil;
import com.ssafy.hebees.domain.ingest.dto.response.IngestRunProgressResponse;
import com.ssafy.hebees.domain.ingest.service.IngestRunProgressService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
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
    @Operation(summary = "진행 상황 조회", description = "JWT 사용자 ID로 진행 중인 run을 찾아 최신 상태를 반환합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "조회 성공"),
        @ApiResponse(responseCode = "401", description = "인증 필요"),
        @ApiResponse(responseCode = "404", description = "진행 중인 run 없음")
    })
    public ResponseEntity<BaseResponse<IngestRunProgressResponse>> getMyRunProgress() {
        var userUuid = SecurityUtil.getCurrentUserUuid()
            .orElseThrow(() -> new RuntimeException("인증된 사용자 없음"));
        IngestRunProgressResponse response = progressService.getLatestProgressForUser(userUuid);
        return ResponseEntity.ok(BaseResponse.success(response));
    }

    // 진행 상황 SSE 스트리밍 (초기 스냅샷 + 실시간 업데이트)
    @GetMapping(value = "/progress/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    @Operation(summary = "진행 상황 SSE 스트리밍", description = "초기 상태를 보낸 뒤 Redis Stream 기반 실시간 업데이트를 전송합니다.")
    public SseEmitter streamMyRunProgress() {
        var userUuid = SecurityUtil.getCurrentUserUuid()
            .orElseThrow(() -> new RuntimeException("인증된 사용자 없음"));

        // 초기 스냅샷 조회
        IngestRunProgressResponse initial = progressService.getLatestProgressForUser(userUuid);

        // 무제한 타임아웃(프록시 환경에 따라 조정 가능)
        SseEmitter emitter = new SseEmitter(0L);

        java.util.concurrent.ExecutorService executor = java.util.concurrent.Executors.newSingleThreadExecutor(r -> {
            Thread t = new Thread(r, "ingest-sse-" + userUuid);
            t.setDaemon(true);
            return t;
        });

        emitter.onCompletion(executor::shutdown);
        emitter.onTimeout(() -> {
            try { emitter.complete(); } finally { executor.shutdownNow(); }
        });
        emitter.onError(e -> {
            try { emitter.completeWithError(e); } finally { executor.shutdownNow(); }
        });

        try {
            emitter.send(SseEmitter.event().name("initial").data(initial));
        } catch (Exception e) {
            emitter.completeWithError(e);
            return emitter;
        }

        executor.submit(() -> {
            String lastId = initial.id() != null ? initial.id() : "$";
            String runId = initial.runId() != null ? initial.runId().toString() : null;
            if (runId == null) {
                emitter.complete();
                return;
            }
            boolean done = false;
            while (!done && !Thread.currentThread().isInterrupted()) {
                try {
                    var records = progressService.readEvents(runId, lastId, 10000L, 10L);
                    if (records != null && !records.isEmpty()) {
                        for (var rec : records) {
                            var dto = IngestRunProgressResponse.from(rec);
                            lastId = rec.getId().getValue();
                            try {
                                emitter.send(SseEmitter.event().name("progress").data(dto));
                            } catch (Exception sendEx) {
                                emitter.completeWithError(sendEx);
                                done = true;
                                break;
                            }
                            String status = dto.status();
                            if (status != null && ("COMPLETED".equalsIgnoreCase(status) || "FAILED".equalsIgnoreCase(status))) {
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
                    try { emitter.completeWithError(e); } catch (Exception ignored) {}
                    done = true;
                }
            }
            try { emitter.complete(); } catch (Exception ignored) {}
        });

        return emitter;
    }
}

