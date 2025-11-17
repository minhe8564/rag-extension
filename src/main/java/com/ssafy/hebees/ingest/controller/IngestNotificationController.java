package com.ssafy.hebees.ingest.controller;

import com.ssafy.hebees.common.exception.BusinessException;
import com.ssafy.hebees.common.exception.ErrorCode;
import com.ssafy.hebees.common.response.BaseResponse;
import com.ssafy.hebees.common.util.SecurityUtil;
import com.ssafy.hebees.ingest.dto.response.IngestNotificationSummaryResponse;
import com.ssafy.hebees.notification.dto.request.NotificationCursorRequest;
import com.ssafy.hebees.notification.dto.response.NotificationCursorResponse;
import com.ssafy.hebees.ingest.service.IngestRunProgressService;
import com.ssafy.hebees.notification.service.NotificationService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.connection.stream.MapRecord;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

@Slf4j
@RestController
@RequestMapping("/ingest/notify")
@RequiredArgsConstructor
@Tag(name = "Ingest", description = "문서 Ingest 알림 및 SSE API")
public class IngestNotificationController {

    private final IngestRunProgressService progressService;
    private final NotificationService notificationService;

    @GetMapping
    @Operation(summary = "Ingest 알림 목록 조회", description = "현재 로그인한 사용자의 ingest 알림을 커서 기반으로 조회합니다.")
    @ApiResponse(responseCode = "200", description = "알림 목록 조회 성공")
    public ResponseEntity<BaseResponse<NotificationCursorResponse>> listNotifications(
        @Valid @ModelAttribute NotificationCursorRequest cursorRequest
    ) {
        UUID userNo = SecurityUtil.getCurrentUserUuid()
            .orElseThrow(() -> new BusinessException(ErrorCode.INVALID_ACCESS_TOKEN));
        NotificationCursorResponse response = notificationService.listNotifications(userNo,
            cursorRequest);
        return ResponseEntity.ok(BaseResponse.success(response));
    }

    /**
     * 현재 로그인한 사용자의 ingest summary 완료(complete == total) 시점을 알림으로 전달하는 SSE. 클라이언트는 로그인 직후 이 스트림을
     * 연결해두고, SUMMARY 이벤트 중 completed >= total 인 이벤트를 알림으로 사용한다.
     */
    @GetMapping(value = "/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    @Operation(summary = "Ingest 완료 알림 SSE", description = "summary completed/total 이 일치하는 시점에만 알림 이벤트를 전송합니다.")
    public SseEmitter streamNotification(HttpServletRequest request) {
        UUID userUuid = SecurityUtil.getCurrentUserUuid()
            .orElseThrow(() -> new RuntimeException("인증된 사용자 없음"));

        String lastIdHeader = request.getHeader("Last-Event-ID");
        String initialSummaryId = progressService.getLatestSummaryId();
        String lastId;
        if (lastIdHeader != null && !lastIdHeader.isBlank()) {
            // 클라이언트가 Last-Event-ID 를 보내면 그 이후부터 재개
            lastId = lastIdHeader;
        } else {
            // 최초 연결 시에는 기존 SUMMARY 레코드는 건너뛰고,
            // 현재 시점 이후로 들어오는 새 SUMMARY 이벤트만 대상으로 삼는다.
            lastId = initialSummaryId != null ? initialSummaryId : "0-0";
        }

        SseEmitter emitter = new SseEmitter(0L);
        ExecutorService executor = Executors.newSingleThreadExecutor(r -> {
            Thread t = new Thread(r, "ingest-notify-sse-" + userUuid);
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

        executor.submit(() -> {
            log.info("[INGEST-NOTIFY] SSE 스트림 루프 시작 - userUuid={}", userUuid);
            String lastSummaryId = lastId;
            boolean running = true;

            try {
                while (running && !Thread.currentThread().isInterrupted()) {
                    try {
                        List<MapRecord<String, Object, Object>> records = progressService.readSummaryEvents(
                            lastSummaryId,
                            2000L,
                            50L
                        );

                        if (records != null && !records.isEmpty()) {
                            for (MapRecord<String, Object, Object> rec : records) {
                                lastSummaryId = rec.getId().getValue();
                                Map<Object, Object> fields = rec.getValue();

                                Object userIdObj = fields.get("userId");
                                if (userIdObj == null || !userUuid.toString()
                                    .equals(userIdObj.toString())) {
                                    continue;
                                }

                                int total = parseInt(fields.get("total"));
                                int completed = parseInt(fields.get("completed"));
                                int success = parseInt(fields.get("successCount"));
                                int failed = parseInt(fields.get("failedCount"));

                                if (total > 0 && completed >= total) {
                                    // ingest summary 완료 시점에 NOTIFICATION 테이블에 저장
                                    notificationService.saveIngestSummaryNotification(
                                        userUuid,
                                        lastSummaryId,
                                        total,
                                        success,
                                        failed
                                    );

                                    IngestNotificationSummaryResponse payload =
                                        new IngestNotificationSummaryResponse(
                                            total,
                                            completed,
                                            success,
                                            failed
                                        );
                                    try {
                                        emitter.send(SseEmitter.event()
                                            .name("ingest-summary-completed")
                                            .id(lastSummaryId)
                                            .data(BaseResponse.success(payload)));
                                        log.info(
                                            "[INGEST-NOTIFY] 완료 알림 전송 - userUuid={}, total={}, completed={}, success={}, failed={}",
                                            userUuid, total, completed, success, failed
                                        );
                                    } catch (Exception sendEx) {
                                        log.warn("[INGEST-NOTIFY] SSE 전송 실패 - userUuid={}",
                                            userUuid, sendEx);
                                        emitter.completeWithError(sendEx);
                                        running = false;
                                        break;
                                    }
                                }
                            }
                        } else {
                            try {
                                emitter.send(SseEmitter.event().comment("keepalive"));
                            } catch (Exception ignore) {
                                // ignore
                            }
                            Thread.sleep(2000L);
                        }
                    } catch (Exception loopEx) {
                        log.warn("[INGEST-NOTIFY] summary 스트림 처리 중 오류 - userUuid={}", userUuid,
                            loopEx);
                        try {
                            emitter.completeWithError(loopEx);
                        } catch (Exception ignored) {
                        }
                        running = false;
                    }
                }
            } finally {
                try {
                    emitter.complete();
                } catch (Exception ignored) {
                }
            }
        });

        return emitter;
    }

    private int parseInt(Object value) {
        try {
            return value == null ? 0 : Integer.parseInt(value.toString());
        } catch (Exception e) {
            return 0;
        }
    }
}
