package com.ssafy.hebees.chat.service;

import com.ssafy.hebees.chat.client.dto.LlmChatMessage;
import com.ssafy.hebees.chat.client.dto.LlmChatResult;
import com.ssafy.hebees.chat.dto.request.AskRequest;
import com.ssafy.hebees.chat.dto.request.MessageCreateRequest;
import com.ssafy.hebees.chat.dto.request.MessageUpdateRequest;
import com.ssafy.hebees.chat.dto.response.AskStreamInitResponse;
import com.ssafy.hebees.chat.dto.response.MessageResponse;
import com.ssafy.hebees.chat.entity.MessageRole;
import com.ssafy.hebees.chat.entity.Session;
import com.ssafy.hebees.chat.repository.MessageRepository;
import com.ssafy.hebees.chat.repository.SessionRepository;
import com.ssafy.hebees.common.exception.BusinessException;
import com.ssafy.hebees.common.exception.ErrorCode;
import com.ssafy.hebees.common.response.BaseResponse;
import com.ssafy.hebees.common.util.ValidationUtil;
import com.ssafy.hebees.dashboard.service.GenerationHistoryStreamPublisher;
import com.ssafy.hebees.ragsetting.repository.StrategyRepository;
import java.io.IOException;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import java.util.concurrent.CompletableFuture;
import java.util.function.Consumer;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

@Slf4j
@Service
@RequiredArgsConstructor
public class ChatAskStreamService {

    private final SessionRepository sessionRepository;
    private final MessageService messageService;
    private final MessageRepository messageRepository;
    private final LlmChatGateway llmChatGateway;
    private final StrategyRepository strategyRepository;
    private final GenerationHistoryStreamPublisher generationHistoryStreamPublisher;

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
        MessageResponse aiPlaceholder = null;
        UUID llmNo = null;
        String sanitizedQuery;

        try {
            ValidationUtil.require(userNo);
            ValidationUtil.require(sessionNo);
            sanitizedQuery = sanitize(request.getQuery());

            Session session = sessionRepository.findBySessionNo(sessionNo)
                .orElseThrow(() -> new BusinessException(ErrorCode.SESSION_NOT_FOUND));

            if (!session.getUserNo().equals(userNo)) {
                throw new BusinessException(ErrorCode.OWNER_ACCESS_DENIED);
            }

            session.updateLastRequestedAt(LocalDateTime.now());
            sessionRepository.save(session);

            generationHistoryStreamPublisher.publishQuery(userNo, sessionNo, sanitizedQuery);

            messageService.createMessage(sessionNo, buildHumanMessage(userNo, sanitizedQuery));

            List<LlmChatMessage> llmMessages = toChatMessages(
                messageService.getAllMessages(userNo, sessionNo));

            if (llmMessages.isEmpty()) {
                log.error("LLM에 전달할 메시지가 없습니다. sessionNo={}, userNo={}", sessionNo, userNo);
                throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
            }

            llmNo = resolveLlmNo(request);

            aiPlaceholder = messageService.createMessage(sessionNo,
                buildAiPlaceholderMessage(llmNo));

            sendInit(emitter, aiPlaceholder);

            Consumer<String> chunkConsumer = chunk -> sendContentUpdate(emitter, chunk);

            LlmChatResult llmResult = llmChatGateway.streamChat(userNo, llmNo, llmMessages,
                chunkConsumer);

            messageService.updateMessage(sessionNo, aiPlaceholder.messageNo(),
                buildAiUpdate(llmResult, llmNo));

            generationHistoryStreamPublisher.publishMetrics(userNo, sessionNo, llmNo, llmResult);

            safeComplete(emitter);
        } catch (StreamDeliveryException streamDeliveryException) {
            log.debug("ask/stream delivery halted for sessionNo={}", sessionNo,
                streamDeliveryException);
            if (aiPlaceholder != null) {
                deleteMessageQuietly(sessionNo, aiPlaceholder.messageNo());
            }
        } catch (BusinessException ex) {
            log.warn("ask/stream failed: sessionNo={}, reason={}", sessionNo, ex.getMessage());
            generationHistoryStreamPublisher.publishError(
                userNo,
                sessionNo,
                llmNo,
                request.getQuery(),
                ex.getErrorCode(),
                ex
            );
            if (aiPlaceholder != null) {
                deleteMessageQuietly(sessionNo, aiPlaceholder.messageNo());
            }
            sendError(emitter, ex.getErrorCode(), ex.getMessage());
        } catch (Exception ex) {
            log.error("Unexpected error during ask/stream processing", ex);
            generationHistoryStreamPublisher.publishError(
                userNo,
                sessionNo,
                llmNo,
                request.getQuery(),
                ErrorCode.INTERNAL_SERVER_ERROR,
                ex
            );
            if (aiPlaceholder != null) {
                deleteMessageQuietly(sessionNo, aiPlaceholder.messageNo());
            }
            sendError(emitter, ErrorCode.INTERNAL_SERVER_ERROR,
                ErrorCode.INTERNAL_SERVER_ERROR.getMessage());
        }
    }

    private void sendInit(SseEmitter emitter, MessageResponse aiPlaceholder) {
        AskStreamInitResponse initPayload = new AskStreamInitResponse(
            aiPlaceholder.messageNo(),
            aiPlaceholder.role() != null ? aiPlaceholder.role().getValue() : MessageRole.AI.getValue(),
            aiPlaceholder.createdAt()
        );
        try {
            emitter.send(SseEmitter.event().name("init").data(initPayload));
        } catch (IOException e) {
            throw new StreamDeliveryException("Failed to send init event", e);
        }
    }

    private void sendContentUpdate(SseEmitter emitter, String content) {
        try {
            emitter.send(SseEmitter.event().name("update").data(Map.of("content", content)));
        } catch (IOException e) {
            throw new StreamDeliveryException("Failed to send update event", e);
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
            safeComplete(emitter);
        }
    }

    private MessageCreateRequest buildHumanMessage(UUID userNo, String content) {
        return MessageCreateRequest.builder()
            .role(MessageRole.HUMAN)
            .content(content)
            .userNo(userNo)
            .build();
    }

    private MessageCreateRequest buildAiPlaceholderMessage(UUID llmNo) {
        return MessageCreateRequest.builder()
            .role(MessageRole.AI)
            .content("")
            .llmNo(llmNo)
            .build();
    }

    private MessageUpdateRequest buildAiUpdate(LlmChatResult result, UUID llmNo) {
        return MessageUpdateRequest.builder()
            .role(MessageRole.AI)
            .content(result.content())
            .llmNo(llmNo)
            .inputTokens(result.inputTokens())
            .outputTokens(result.outputTokens())
            .totalTokens(result.totalTokens())
            .responseTimeMs(result.responseTimeMs())
            .build();
    }

    private List<LlmChatMessage> toChatMessages(List<MessageResponse> history) {
        return history.stream()
            .map(this::toChatMessage)
            .filter(Optional::isPresent)
            .map(Optional::get)
            .toList();
    }

    private Optional<LlmChatMessage> toChatMessage(MessageResponse message) {
        if (message == null || !StringUtils.hasText(message.content())) {
            return Optional.empty();
        }

        MessageRole role = message.role();
        String mappedRole = switch (role) {
            case HUMAN -> "user";
            case AI -> "assistant";
            case SYSTEM -> "system";
            case TOOL -> "tool";
        };

        return Optional.of(new LlmChatMessage(mappedRole, message.content()));
    }

    private UUID resolveLlmNo(AskRequest request) {
        UUID llmNo = request.llmNo();
        if (StringUtils.hasText(request.model())) {
            return strategyRepository.findByNameAndCodeStartingWith(request.model(), "GEN")
                .orElseThrow(() -> new BusinessException(ErrorCode.BAD_REQUEST))
                .getStrategyNo();
        }
        if (llmNo == null) {
            throw new BusinessException(ErrorCode.BAD_REQUEST);
        }
        return llmNo;
    }

    private String sanitize(String text) {
        if (!StringUtils.hasText(text)) {
            throw new BusinessException(ErrorCode.INPUT_BLANK);
        }
        return text.trim();
    }

    void deleteMessageQuietly(UUID sessionNo, UUID messageNo) {
        messageRepository.findBySessionNoAndMessageNo(sessionNo, messageNo)
            .ifPresent(messageRepository::delete);
    }

    private void safeComplete(SseEmitter emitter) {
        try {
            emitter.complete();
        } catch (IllegalStateException ignore) {
            // already completed
        }
    }

    private static class StreamDeliveryException extends RuntimeException {

        private StreamDeliveryException(String message, Throwable cause) {
            super(message, cause);
        }
    }
}

