package com.ssafy.hebees.chat.service;

import com.ssafy.hebees.chat.client.dto.LlmChatMessage;
import com.ssafy.hebees.chat.client.dto.LlmChatResult;
import com.ssafy.hebees.chat.dto.request.AskRequest;
import com.ssafy.hebees.chat.dto.request.MessageCreateRequest;
import com.ssafy.hebees.chat.dto.response.AskResponse;
import com.ssafy.hebees.chat.dto.response.MessageResponse;
import com.ssafy.hebees.chat.entity.MessageRole;
import com.ssafy.hebees.chat.entity.Session;
import com.ssafy.hebees.chat.repository.SessionRepository;
import com.ssafy.hebees.common.util.ValidationUtil;
import com.ssafy.hebees.common.exception.BusinessException;
import com.ssafy.hebees.common.exception.ErrorCode;
import com.ssafy.hebees.ragsetting.entity.Strategy;
import com.ssafy.hebees.ragsetting.repository.StrategyRepository;
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
    private final LlmChatGateway llmChatGateway;
    private final StrategyRepository strategyRepository;

    @Override
    public AskResponse ask(UUID userNo, UUID sessionNo, AskRequest request) {
        ValidationUtil.require(userNo);
        ValidationUtil.require(sessionNo);
        String sanitizedQuery = sanitize(request.getQuery());

        Session session = sessionRepository.findBySessionNo(sessionNo)
            .orElseThrow(() -> new BusinessException(ErrorCode.SESSION_NOT_FOUND));

        // 자신의 채팅방이 아니면 채팅 불가
        if (!session.getUserNo().equals(userNo)) {
            log.warn("세션 접근 거부: requester={}, sessionNo={}", userNo, sessionNo);
            throw new BusinessException(ErrorCode.OWNER_ACCESS_DENIED);
        }

        session.updateLastRequestedAt(LocalDateTime.now());

        // 사용자 메시지 저장
        messageService.createMessage(sessionNo,
            buildHumanMessage(userNo, sanitizedQuery));

        // 대화 이력 조회
        List<MessageResponse> history = messageService.getAllMessages(userNo, sessionNo);
        List<LlmChatMessage> llmMessages = history.stream()
            .map(this::toChatMessage)
            .filter(Optional::isPresent)
            .map(Optional::get)
            .toList();

        // 사용자 질문 저장 실패
        if (llmMessages.isEmpty()) {
            log.error("LLM에 전달할 메시지가 없습니다. sessionNo={}, userNo={}", sessionNo, userNo);
            throw new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR);
        }

        UUID llmNo = request.llmNo();
        if (StringUtils.hasText(request.model())) {
            llmNo = strategyRepository.findByNameAndCodeStartingWith(request.model(), "GEN")
                .orElseThrow(() -> new BusinessException(ErrorCode.BAD_REQUEST)).getStrategyNo();
        }

        LlmChatResult llmResult = llmChatGateway.chat(userNo, llmNo, llmMessages);
        String answer = Optional.ofNullable(llmResult.content()).orElse("");

        MessageResponse aiMessage = messageService.createMessage(sessionNo,
            buildAiMessage(
                request.llmNo(),
                answer,
                llmResult.inputTokens(),
                llmResult.outputTokens(),
                llmResult.totalTokens(),
                llmResult.responseTimeMs()
            ));

        return new AskResponse(
            aiMessage.messageNo(),
            aiMessage.role().getValue(),
            aiMessage.content(),
            aiMessage.createdAt()
        );
    }

    private MessageCreateRequest buildHumanMessage(UUID userNo, String content) {
        return MessageCreateRequest.builder()
            .role(MessageRole.HUMAN)
            .content(content)
            .userNo(userNo)
            .build();
    }

    private MessageCreateRequest buildAiMessage(
        UUID llmNo,
        String content,
        Long inputTokens,
        Long outputTokens,
        Long totalTokens,
        Long responseTimeMs
    ) {
        return MessageCreateRequest.builder()
            .role(MessageRole.AI)
            .content(content)
            .llmNo(llmNo)
            .inputTokens(inputTokens)
            .outputTokens(outputTokens)
            .totalTokens(totalTokens)
            .responseTimeMs(responseTimeMs)
            .build();
    }

    private Optional<LlmChatMessage> toChatMessage(MessageResponse message) {
        if (message == null || !StringUtils.hasText(message.content())) {
            return Optional.empty();
        }

        String role = switch (message.role()) {
            case HUMAN -> "user";
            case AI -> "assistant";
            case SYSTEM -> "system";
            case TOOL -> "tool";
        };

        return Optional.of(new LlmChatMessage(role, message.content()));
    }

    private String sanitize(String text) {
        if (!StringUtils.hasText(text)) {
            throw new BusinessException(ErrorCode.INPUT_BLANK);
        }
        return text.trim();
    }
}

