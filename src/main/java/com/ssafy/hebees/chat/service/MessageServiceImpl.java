package com.ssafy.hebees.chat.service;

import com.ssafy.hebees.chat.dto.request.MessageCreateRequest;
import com.ssafy.hebees.chat.dto.request.MessageCursorRequest;
import com.ssafy.hebees.chat.dto.response.MessageCursorResponse;
import com.ssafy.hebees.chat.dto.response.MessageResponse;
import com.ssafy.hebees.chat.dto.response.ReferencedDocumentListResponse;
import com.ssafy.hebees.chat.dto.response.ReferencedDocumentResponse;
import com.ssafy.hebees.chat.entity.Message;
import com.ssafy.hebees.chat.entity.MessageReference;
import com.ssafy.hebees.chat.repository.MessageRepository;
import com.ssafy.hebees.chat.repository.SessionRepository;
import com.ssafy.hebees.common.exception.BusinessException;
import com.ssafy.hebees.common.exception.ErrorCode;
import com.ssafy.hebees.common.util.ValidationUtil;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Slf4j
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class MessageServiceImpl implements MessageService {

    private final MessageRepository messageRepository;
    private final SessionRepository sessionRepository;

    @Override
    @Transactional
    public MessageResponse createMessage(UUID sessionNo, MessageCreateRequest request) {
        UUID sessionId = ValidationUtil.require(sessionNo);

        if (request.userNo() != null) {
            validateOwnership(request.userNo(), sessionId);
        }

        Message message = toMessage(sessionId, request);

        Message saved = messageRepository.save(message);

        return toMessageResponse(saved);
    }

    @Override
    public MessageCursorResponse listMessages(UUID userNo, UUID sessionNo,
        MessageCursorRequest request) {
        UUID owner = ValidationUtil.require(userNo);
        UUID sessionId = ValidationUtil.require(sessionNo);

        validateOwnership(owner, sessionId);

        MessageCursorRequest effectiveRequest = request != null
            ? request
            : new MessageCursorRequest(null, null);

        int requestedSize = effectiveRequest.limit();
        LocalDateTime cursor = effectiveRequest.cursor();

        int fetchSize = requestedSize + 1;
        Pageable pageable = PageRequest.of(0, fetchSize, Sort.by(Sort.Direction.DESC, "createdAt"));

        List<Message> fetched = cursor == null
            ? messageRepository.findBySessionNoOrderByCreatedAtDesc(sessionId, pageable)
            : messageRepository.findBySessionNoAndCreatedAtBeforeOrderByCreatedAtDesc(sessionId,
                cursor, pageable);

        boolean hasNext = fetched.size() > requestedSize;
        List<Message> limited = hasNext
            ? new ArrayList<>(fetched.subList(0, requestedSize))
            : new ArrayList<>(fetched);

        LocalDateTime nextCursor = hasNext && !limited.isEmpty()
            ? limited.getLast().getCreatedAt()
            : null;

        Collections.reverse(limited);

        List<MessageResponse> data = limited.stream()
            .map(MessageServiceImpl::toMessageResponse)
            .toList();

        return new MessageCursorResponse(
            data,
            new MessageCursorResponse.Pagination(nextCursor, hasNext, data.size())
        );
    }

    @Override
    public MessageResponse getMessage(UUID userNo, UUID sessionNo, UUID messageNo) {
        UUID owner = ValidationUtil.require(userNo);
        UUID sessionId = ValidationUtil.require(sessionNo);
        UUID messageId = ValidationUtil.require(messageNo);

        validateOwnership(owner, sessionId);

        Message chatMessage = messageRepository.findBySessionNoAndMessageNo(sessionId,
                messageId)
            .orElseThrow(() -> {
                log.warn("메시지 조회 실패 - 존재하지 않음: sessionNo={}, messageNo={}", sessionId, messageId);
                return new BusinessException(ErrorCode.NOT_FOUND);
            });

        return toMessageResponse(chatMessage);
    }

    @Override
    public ReferencedDocumentListResponse listReferencedDocuments(UUID userNo, UUID sessionNo,
        UUID messageNo) {
        MessageResponse message = getMessage(userNo, sessionNo, messageNo);
        return toReferencedDocumentListResponse(message.references());
    }

    @Override
    public ReferencedDocumentResponse getReferencedDocument(UUID userNo, UUID sessionNo,
        UUID messageNo, UUID documentNo) {
        UUID docId = ValidationUtil.require(documentNo);

        return listReferencedDocuments(userNo, sessionNo, messageNo).data().stream()
            .filter(doc -> Objects.equals(doc.fileNo(), docId))
            .findFirst()
            .orElseThrow(() -> {
                log.warn("참조 문서 조회 실패 - 존재하지 않음: messageNo={}, documentNo={}", messageNo,
                    docId);
                return new BusinessException(ErrorCode.NOT_FOUND);
            });
    }

    @Override
    public List<MessageResponse> getAllMessages(UUID userNo, UUID sessionNo) {
        UUID owner = ValidationUtil.require(userNo);
        UUID sessionId = ValidationUtil.require(sessionNo);

        validateOwnership(owner, sessionId);

        return messageRepository.findBySessionNoOrderByCreatedAtAsc(sessionId).stream()
            .map(MessageServiceImpl::toMessageResponse)
            .toList();
    }

    private void validateOwnership(UUID userNo, UUID sessionNo) {
        sessionRepository.findBySessionNo(sessionNo)
            .map(session -> {
                if (!session.getUserNo().equals(userNo)) {
                    log.warn("세션 접근 거부: requester={}, sessionNo={}", userNo, sessionNo);
                    throw new BusinessException(ErrorCode.OWNER_ACCESS_DENIED);
                }
                return session;
            })
            .orElseThrow(() -> {
                log.warn("세션 조회 실패 - 존재하지 않음: sessionNo={}", sessionNo);
                return new BusinessException(ErrorCode.NOT_FOUND);
            });
    }

    private Message toMessage(UUID sessionNo, MessageCreateRequest request) {
        List<MessageReference> references = request.references() == null ? null : request.references().stream()
            .map(ref -> MessageReference.builder()
                .fileNo(ref.fileNo())
                .name(ref.name())
                .title(ref.title())
                .type(ref.type())
                .index(ref.index())
                .downloadUrl(ref.downloadUrl())
                .snippet(ref.snippet())
                .build()).toList();

        return Message.builder()
            .sessionNo(sessionNo)
            .messageNo(UUID.randomUUID())
            .role(request.role())
            .content(request.content())
            .userNo(request.userNo())
            .llmNo(request.llmNo())
            .inputTokens(request.inputTokens())
            .outputTokens(request.outputTokens())
            .totalTokens(request.totalTokens())
            .responseTimeMs(request.responseTimeMs())
            .referencedDocuments(references)
            .build();
    }

    private static MessageResponse toMessageResponse(Message message) {
        List<ReferencedDocumentResponse> references = Optional.ofNullable(
                message.getReferencedDocuments())
            .orElseGet(List::of)
            .stream()
            .map(ref -> new ReferencedDocumentResponse(
                ref.getFileNo(),
                ref.getName(),
                ref.getTitle(),
                ref.getType(),
                ref.getIndex(),
                ref.getDownloadUrl(),
                ref.getSnippet()
            )).toList();

        return MessageResponse.builder()
            .messageNo(message.getMessageNo())
            .role(message.getRole())
            .userNo(message.getUserNo())
            .llmNo(message.getLlmNo())
            .content(message.getContent())
            .createdAt(message.getCreatedAt())
            .references(references)
            .build();
    }

    private static ReferencedDocumentListResponse toReferencedDocumentListResponse(
        List<ReferencedDocumentResponse> documents
    ) {
        return new ReferencedDocumentListResponse(documents);
    }
}

