package com.ssafy.hebees.chat.service;

import com.ssafy.hebees.chat.dto.request.MessageCreateRequest;
import com.ssafy.hebees.chat.dto.request.MessageCursorRequest;
import com.ssafy.hebees.chat.dto.request.MessageUpdateRequest;
import com.ssafy.hebees.chat.dto.response.MessageCursorResponse;
import com.ssafy.hebees.chat.dto.response.MessageResponse;
import com.ssafy.hebees.chat.dto.response.ReferencedDocumentListResponse;
import com.ssafy.hebees.chat.dto.response.ReferencedDocumentResponse;
import com.ssafy.hebees.chat.entity.Message;
import com.ssafy.hebees.chat.entity.MessageReference;
import com.ssafy.hebees.chat.entity.Session;
import com.ssafy.hebees.chat.repository.MessageRepository;
import com.ssafy.hebees.chat.repository.SessionRepository;
import com.ssafy.hebees.common.exception.BusinessException;
import com.ssafy.hebees.common.exception.ErrorCode;
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
        UUID sessionId = requireSession(sessionNo);
        Session session = sessionRepository.findBySessionNo(sessionId)
            .orElseThrow(() -> {
                log.warn("세션 조회 실패 - 존재하지 않음: sessionNo={}", sessionId);
                return new BusinessException(ErrorCode.NOT_FOUND);
            });
        return createMessage(session.getUserNo(), sessionId, request);
    }

    @Override
    @Transactional
    public MessageResponse createMessage(UUID userNo, UUID sessionNo,
        MessageCreateRequest request) {
        UUID owner = requireUser(userNo);
        UUID sessionId = requireSession(sessionNo);

        validateOwnership(owner, sessionId);

        UUID author = Optional.ofNullable(request.userNo()).orElse(owner);

        List<MessageReference> references = mapToReferences(request);

        Message message = Message.builder()
            .sessionNo(sessionId)
            .messageNo(UUID.randomUUID())
            .role(request.role())
            .content(request.content())
            .userNo(author)
            .llmNo(request.llmNo())
            .inputTokens(request.inputTokens())
            .outputTokens(request.outputTokens())
            .totalTokens(request.totalTokens())
            .responseTimeMs(request.responseTimeMs())
            .referencedDocuments(new ArrayList<>(references))
            .build();

        Message saved = messageRepository.save(message);

        return toMessageResponse(saved);
    }

    @Override
    public MessageCursorResponse listMessages(UUID userNo, UUID sessionNo,
        MessageCursorRequest request) {
        UUID owner = requireUser(userNo);
        UUID sessionId = requireSession(sessionNo);

        validateOwnership(owner, sessionId);

        MessageCursorRequest effectiveRequest = request != null
            ? request
            : new MessageCursorRequest(null, null);

        int requestedSize = effectiveRequest.limit();
        LocalDateTime cursor = effectiveRequest.cursor();

        int fetchSize = requestedSize + 1;
        Pageable pageable = PageRequest.of(0, fetchSize,
            Sort.by(Sort.Direction.DESC, "createdAt"));

        List<Message> fetched = cursor == null
            ? messageRepository.findBySessionNoOrderByCreatedAtDesc(sessionId, pageable)
            : messageRepository.findBySessionNoAndCreatedAtBeforeOrderByCreatedAtDesc(sessionId, cursor,
                pageable);

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

        MessageCursorResponse.Pagination pagination =
            new MessageCursorResponse.Pagination(nextCursor, hasNext, data.size());
        return new MessageCursorResponse(data, pagination);
    }

    @Override
    @Transactional
    public MessageResponse updateMessage(UUID sessionNo, UUID messageNo,
        MessageUpdateRequest request) {
        UUID sessionId = requireSession(sessionNo);
        UUID target = requireMessage(messageNo);

        Message existing = messageRepository.findBySessionNoAndMessageNo(sessionId, target)
            .orElseThrow(() -> {
                log.warn("메시지 업데이트 실패 - 존재하지 않음: sessionNo={}, messageNo={}", sessionId, target);
                return new BusinessException(ErrorCode.NOT_FOUND);
            });

        Message updated = existing.toBuilder()
            .role(Optional.ofNullable(request.role()).orElse(existing.getRole()))
            .content(Optional.ofNullable(request.content()).orElse(existing.getContent()))
            .userNo(Optional.ofNullable(request.userNo()).orElse(existing.getUserNo()))
            .llmNo(Optional.ofNullable(request.llmNo()).orElse(existing.getLlmNo()))
            .inputTokens(Optional.ofNullable(request.inputTokens()).orElse(existing.getInputTokens()))
            .outputTokens(Optional.ofNullable(request.outputTokens()).orElse(existing.getOutputTokens()))
            .totalTokens(Optional.ofNullable(request.totalTokens()).orElse(existing.getTotalTokens()))
            .responseTimeMs(Optional.ofNullable(request.responseTimeMs()).orElse(existing.getResponseTimeMs()))
            .referencedDocuments(new ArrayList<>(resolveReferences(existing, request)))
            .build();

        Message saved = messageRepository.save(updated);
        return toMessageResponse(saved);
    }

    @Override
    public MessageResponse getMessage(UUID userNo, UUID sessionNo, UUID messageNo) {
        UUID owner = requireUser(userNo);
        UUID sessionId = requireSession(sessionNo);
        UUID messageId = requireMessage(messageNo);

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
        UUID docId = requireDocument(documentNo);

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
        UUID owner = requireUser(userNo);
        UUID sessionId = requireSession(sessionNo);

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
                    throw new BusinessException(ErrorCode.PERMISSION_DENIED);
                }
                return session;
            })
            .orElseThrow(() -> {
                log.warn("세션 조회 실패 - 존재하지 않음: sessionNo={}", sessionNo);
                return new BusinessException(ErrorCode.NOT_FOUND);
            });
    }

    private UUID requireUser(UUID userNo) {
        if (userNo == null) {
            throw new BusinessException(ErrorCode.UNAUTHORIZED);
        }
        return userNo;
    }

    private UUID requireSession(UUID sessionNo) {
        if (sessionNo == null) {
            throw new BusinessException(ErrorCode.INVALID_INPUT);
        }
        return sessionNo;
    }

    private UUID requireMessage(UUID messageNo) {
        if (messageNo == null) {
            throw new BusinessException(ErrorCode.INVALID_INPUT);
        }
        return messageNo;
    }

    private UUID requireDocument(UUID documentNo) {
        if (documentNo == null) {
            throw new BusinessException(ErrorCode.INVALID_INPUT);
        }
        return documentNo;
    }

    private List<MessageReference> mapToReferences(MessageCreateRequest request) {
        return toReferenceEntities(request != null ? request.references() : null);
    }

    private List<MessageReference> mapToReferences(MessageUpdateRequest request) {
        return toReferenceEntities(request != null ? request.references() : null);
    }

    private List<MessageReference> toReferenceEntities(
        List<MessageCreateRequest.ReferencedDocumentCreateRequest> references
    ) {
        if (references == null || references.isEmpty()) {
            return List.of();
        }

        return references.stream()
            .map(ref -> MessageReference.builder()
                .fileNo(ref.fileNo())
                .name(ref.name())
                .title(ref.title())
                .type(ref.type())
                .index(ref.index())
                .downloadUrl(ref.downloadUrl())
                .snippet(ref.snippet())
                .build())
            .toList();
    }

    private List<MessageReference> resolveReferences(Message existing, MessageUpdateRequest request) {
        if (request == null || request.references() == null) {
            return existing.getReferencedDocuments();
        }
        return mapToReferences(request);
    }

    private static MessageResponse toMessageResponse(Message chatMessage) {
        List<ReferencedDocumentResponse> references = Optional.ofNullable(
                chatMessage.getReferencedDocuments())
            .orElseGet(List::of)
            .stream()
            .map(MessageServiceImpl::toReferencedDocumentResponse)
            .toList();

        return new MessageResponse(
            chatMessage.getMessageNo(),
            chatMessage.getRole(),
            chatMessage.getUserNo(),
            chatMessage.getLlmNo(),
            chatMessage.getContent(),
            chatMessage.getCreatedAt(),
            references
        );
    }

    private static ReferencedDocumentResponse toReferencedDocumentResponse(
        MessageReference reference) {
        return new ReferencedDocumentResponse(
            reference.getFileNo(),
            reference.getName(),
            reference.getTitle(),
            reference.getType(),
            reference.getIndex(),
            reference.getDownloadUrl(),
            reference.getSnippet()
        );
    }

    private static ReferencedDocumentListResponse toReferencedDocumentListResponse(
        List<ReferencedDocumentResponse> documents
    ) {
        return new ReferencedDocumentListResponse(documents);
    }
}

