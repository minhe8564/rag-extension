package com.ssafy.hebees.chat.service;

import com.ssafy.hebees.chat.dto.request.AskRequest;
import com.ssafy.hebees.chat.dto.response.AskResponse;
import com.ssafy.hebees.chat.dto.response.AskStreamInitResponse;
import com.ssafy.hebees.common.exception.BusinessException;
import com.ssafy.hebees.common.exception.ErrorCode;
import com.ssafy.hebees.common.response.BaseResponse;
import java.io.IOException;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.CompletableFuture;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

@Slf4j
@Service
@RequiredArgsConstructor
public class ChatAskStreamService {

    private final ChatAskService chatAskService;

    public SseEmitter askStream(UUID userNo, UUID pathSessionNo, AskRequest request) {
        SseEmitter emitter = new SseEmitter(0L);
        emitter.onTimeout(emitter::complete);
        emitter.onError(error -> log.warn("ask/stream SSE error", error));

        UUID effectiveSessionNo = pathSessionNo != null ? pathSessionNo : request.sessionNo();
        if (effectiveSessionNo == null) {
            sendError(emitter, ErrorCode.BAD_REQUEST, ErrorCode.BAD_REQUEST.getMessage());
            return emitter;
        }

        CompletableFuture.runAsync(() ->
            processStream(emitter, userNo, effectiveSessionNo, request)
        );

        return emitter;
    }

    private void processStream(SseEmitter emitter, UUID userNo, UUID sessionNo,
        AskRequest request) {
        try {
            AskResponse response = chatAskService.ask(userNo, sessionNo, request);
            emitter.send(
                SseEmitter.event().name("init").data(AskStreamInitResponse.from(response)));

            streamContent(emitter, response.content());
            emitter.complete();
        } catch (BusinessException ex) {
            sendError(emitter, ex.getErrorCode(), ex.getMessage());
        } catch (IOException ex) {
            log.warn("Failed to send ask/stream SSE event", ex);
            sendError(emitter, ErrorCode.INTERNAL_SERVER_ERROR,
                ErrorCode.INTERNAL_SERVER_ERROR.getMessage());
        } catch (Exception ex) {
            log.error("Unexpected error during ask/stream processing", ex);
            sendError(emitter, ErrorCode.INTERNAL_SERVER_ERROR,
                ErrorCode.INTERNAL_SERVER_ERROR.getMessage());
        }
    }

    private void streamContent(SseEmitter emitter, String content) throws IOException {
        if (!StringUtils.hasText(content)) {
            emitter.send(SseEmitter.event().name("update").data(Map.of("content", "")));
            return;
        }

        int length = content.length();
        int chunkSize = Math.max(5, Math.min(80, Math.max(1, length / 5)));

        for (int start = 0; start < length; start += chunkSize) {
            int end = Math.min(start + chunkSize, length);
            String segment = content.substring(start, end);
            emitter.send(SseEmitter.event().name("update").data(Map.of("content", segment)));
            if (end < length) {
                sleepQuietly(60L);
            }
        }
    }

    private void sendError(SseEmitter emitter, ErrorCode errorCode, String message) {
        BaseResponse<Object> errorPayload = BaseResponse.error(
            errorCode.getStatus(),
            errorCode.name(),
            StringUtils.hasText(message) ? message : errorCode.getMessage(),
            null
        );
        try {
            emitter.send(SseEmitter.event().name("error").data(errorPayload));
        } catch (IOException ioException) {
            log.warn("Failed to send SSE error event", ioException);
        } finally {
            emitter.complete();
        }
    }

    private void sleepQuietly(long millis) {
        try {
            Thread.sleep(millis);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}

