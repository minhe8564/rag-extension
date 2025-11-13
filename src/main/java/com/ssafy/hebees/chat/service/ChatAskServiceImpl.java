package com.ssafy.hebees.chat.service;

import com.ssafy.hebees.chat.client.RunpodClient;
import com.ssafy.hebees.chat.client.dto.RunpodChatMessage;
import com.ssafy.hebees.chat.client.dto.RunpodChatResult;
import com.ssafy.hebees.chat.dto.request.MessageCreateRequest;
import com.ssafy.hebees.chat.dto.response.AskResponse;
import com.ssafy.hebees.chat.dto.response.MessageResponse;
import com.ssafy.hebees.chat.entity.MessageRole;
import com.ssafy.hebees.chat.entity.Session;
import com.ssafy.hebees.chat.repository.SessionRepository;
import com.ssafy.hebees.dashboard.model.service.ChatbotUsageStreamService;
import com.ssafy.hebees.common.exception.BusinessException;
import com.ssafy.hebees.common.exception.ErrorCode;
import com.ssafy.hebees.common.util.UserValidationUtil;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

@Slf4j
@Service
@RequiredArgsConstructor
@Transactional
public class ChatAskServiceImpl implements ChatAskService {

    private final SessionRepository sessionRepository;
    private final MessageService messageService;
    private final RunpodClient runpodClient;
    private final ChatbotUsageStreamService chatbotUsageStreamService;

    @Override
    public AskResponse ask(UUID userNo, UUID sessionNo, String question) {
        UserValidationUtil.requireUser(userNo);
        UUID owner = userNo;
        UUID sessionId = requireSession(sessionNo);
        String sanitizedQuestion = sanitize(question);

        Session session = sessionRepository.findBySessionNo(sessionId)
            .orElseThrow(() -> new BusinessException(ErrorCode.NOT_FOUND));

        if (!session.getUserNo().equals(owner)) {
            log.warn("세션 접근 거부: requester={}, sessionNo={}", owner, sessionId);
            throw new BusinessException(ErrorCode.PERMISSION_DENIED);
        }

        session.updateLastRequestedAt(LocalDateTime.now());

        chatbotUsageStreamService.recordChatbotRequest(owner, sessionId);

        // 사용자 메시지 저장
        messageService.createMessage(owner, sessionId,
            buildHumanMessage(owner, session, sanitizedQuestion));

        // 대화 이력 조회
        List<MessageResponse> history = messageService.getAllMessages(owner, sessionId);
        List<RunpodChatMessage> runpodMessages = history.stream()
            .map(this::toRunpodMessage)
            .filter(Optional::isPresent)
            .map(Optional::get)
            .toList();

        if (runpodMessages.isEmpty()) {
            log.error("Runpod에 전달할 메시지가 없습니다. sessionNo={}, userNo={}", sessionId, owner);
            throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
        }

        RunpodChatResult runpodResponse = runpodClient.chat(runpodMessages);
        String answer = sanitize(runpodResponse.content());

        MessageResponse aiMessage = messageService.createMessage(owner, sessionId,
            buildAiMessage(owner, session, answer));

        LocalDateTime timestamp = Optional.ofNullable(aiMessage.createdAt())
            .orElseGet(LocalDateTime::now);

        return new AskResponse(answer, timestamp);
    }

    private MessageCreateRequest buildHumanMessage(UUID owner, Session session, String content) {
        return new MessageCreateRequest(
            MessageRole.HUMAN,
            content,
            owner,
            session.getLlmNo(),
            null,
            null,
            null,
            null,
            List.of()
        );
    }

    private MessageCreateRequest buildAiMessage(UUID owner, Session session, String content) {
        return new MessageCreateRequest(
            MessageRole.AI,
            content,
            owner,
            session.getLlmNo(),
            null,
            null,
            null,
            null,
            List.of()
        );
    }

    private Optional<RunpodChatMessage> toRunpodMessage(MessageResponse message) {
        if (message == null || !StringUtils.hasText(message.content())) {
            return Optional.empty();
        }

        String role = switch (message.role()) {
            case HUMAN -> "user";
            case AI -> "assistant";
            case SYSTEM -> "system";
            case TOOL -> "tool";
        };

        return Optional.of(RunpodChatMessage.of(role, message.content()));
    }

    private UUID requireSession(UUID sessionNo) {
        if (sessionNo == null) {
            throw new BusinessException(ErrorCode.INVALID_INPUT);
        }
        return sessionNo;
    }

    private String sanitize(String text) {
        if (!StringUtils.hasText(text)) {
            throw new BusinessException(ErrorCode.INVALID_INPUT);
        }
        return text.trim();
    }
}

