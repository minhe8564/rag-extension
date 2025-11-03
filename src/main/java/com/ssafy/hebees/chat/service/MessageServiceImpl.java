package com.ssafy.hebees.chat.service;

//import com.ssafy.hebees.domain.chat.dto.request.MessageCreateRequest;
//import com.ssafy.hebees.domain.chat.dto.request.MessageCursorRequest;
//import com.ssafy.hebees.domain.chat.dto.response.MessageCursorResponse;
//import com.ssafy.hebees.domain.chat.dto.response.MessageResponse;
//import com.ssafy.hebees.domain.chat.dto.response.ReferencedDocumentListResponse;
//import com.ssafy.hebees.domain.chat.dto.response.ReferencedDocumentResponse;
//import com.ssafy.hebees.domain.chat.entity.Message;
//import com.ssafy.hebees.domain.chat.entity.MessageReference;
//import com.ssafy.hebees.domain.chat.repository.MessageRepository;
//import com.ssafy.hebees.domain.chat.repository.SessionRepository;
//import com.ssafy.hebees.global.exception.BusinessException;
//import com.ssafy.hebees.global.exception.ErrorCode;
//import java.util.ArrayList;
//import java.util.Collections;
//import java.util.List;
//import java.util.Objects;
//import java.util.Optional;
//import java.util.UUID;
//import lombok.RequiredArgsConstructor;
//import lombok.extern.slf4j.Slf4j;
//import org.springframework.data.domain.PageRequest;
//import org.springframework.data.domain.Pageable;
//import org.springframework.data.domain.Sort;
//import org.springframework.stereotype.Service;
//import org.springframework.transaction.annotation.Transactional;
//
//@Slf4j
//@Service
//@RequiredArgsConstructor
//@Transactional(readOnly = true)
//public class MessageServiceImpl implements MessageService {
//
//    private final MessageRepository messageRepository;
//    private final SessionRepository sessionRepository;
//
//    @Override
//    @Transactional
//    public MessageResponse createMessage(UUID userNo, UUID sessionNo,
//        MessageCreateRequest request) {
//        UUID owner = requireUser(userNo);
//        UUID sessionId = requireSession(sessionNo);
//
//        validateOwnership(owner, sessionId);
//
//        long nextSeq = determineNextSeq(sessionId);
//
//        UUID author = Optional.ofNullable(request.userNo()).orElse(owner);
//
//        List<MessageReference> references = mapToReferences(request);
//
//        Message message = Message.builder()
//            .sessionNo(sessionId)
//            .messageNo(UUID.randomUUID())
//            .role(request.role())
//            .content(request.content())
//            .seq(nextSeq)
//            .userNo(author)
//            .llmNo(request.llmNo())
//            .inputTokens(request.inputTokens())
//            .outputTokens(request.outputTokens())
//            .totalTokens(request.totalTokens())
//            .responseTimeMs(request.responseTimeMs())
//            .referencedDocuments(new ArrayList<>(references))
//            .build();
//
//        Message saved = messageRepository.save(message);
//
//        return toMessageResponse(saved);
//    }
//
//    @Override
//    public MessageCursorResponse listMessages(UUID userNo, UUID sessionNo,
//        MessageCursorRequest request) {
//        UUID owner = requireUser(userNo);
//        UUID sessionId = requireSession(sessionNo);
//
//        validateOwnership(owner, sessionId);
//
//        MessageCursorRequest effectiveRequest = request != null
//            ? request
//            : new MessageCursorRequest(null, null);
//
//        int requestedSize = effectiveRequest.limit();
//        Long cursor = effectiveRequest.cursor();
//
//        int fetchSize = requestedSize + 1;
//        Pageable pageable = PageRequest.of(0, fetchSize, Sort.by(Sort.Direction.DESC, "seq"));
//
//        List<Message> fetched = cursor == null
//            ? messageRepository.findBySessionNoOrderBySeqDesc(sessionId, pageable)
//            : messageRepository.findBySessionNoAndSeqLessThanOrderBySeqDesc(sessionId, cursor,
//                pageable);
//
//        boolean hasNext = fetched.size() > requestedSize;
//        List<Message> limited = hasNext
//            ? new ArrayList<>(fetched.subList(0, requestedSize))
//            : new ArrayList<>(fetched);
//
//        Long nextCursor = hasNext && !limited.isEmpty() ? limited.getLast().getSeq() : null;
//
//        Collections.reverse(limited);
//
//        List<MessageResponse> data = limited.stream()
//            .map(MessageServiceImpl::toMessageResponse)
//            .toList();
//
//        return new MessageCursorResponse(data, nextCursor, hasNext, data.size());
//    }
//
//    @Override
//    public MessageResponse getMessage(UUID userNo, UUID sessionNo, UUID messageNo) {
//        UUID owner = requireUser(userNo);
//        UUID sessionId = requireSession(sessionNo);
//        UUID messageId = requireMessage(messageNo);
//
//        validateOwnership(owner, sessionId);
//
//        Message chatMessage = messageRepository.findBySessionNoAndMessageNo(sessionId,
//                messageId)
//            .orElseThrow(() -> {
//                log.warn("메시지 조회 실패 - 존재하지 않음: sessionNo={}, messageNo={}", sessionId, messageId);
//                return new BusinessException(ErrorCode.NOT_FOUND);
//            });
//
//        return toMessageResponse(chatMessage);
//    }
//
//    @Override
//    public ReferencedDocumentListResponse listReferencedDocuments(UUID userNo, UUID sessionNo,
//        UUID messageNo) {
//        MessageResponse message = getMessage(userNo, sessionNo, messageNo);
//        return toReferencedDocumentListResponse(message.referencedDocuments());
//    }
//
//    @Override
//    public ReferencedDocumentResponse getReferencedDocument(UUID userNo, UUID sessionNo,
//        UUID messageNo, UUID documentNo) {
//        UUID docId = requireDocument(documentNo);
//
//        return listReferencedDocuments(userNo, sessionNo, messageNo).data().stream()
//            .filter(doc -> Objects.equals(doc.fileNo(), docId))
//            .findFirst()
//            .orElseThrow(() -> {
//                log.warn("참조 문서 조회 실패 - 존재하지 않음: messageNo={}, documentNo={}", messageNo,
//                    docId);
//                return new BusinessException(ErrorCode.NOT_FOUND);
//            });
//    }
//
//    private void validateOwnership(UUID userNo, UUID sessionNo) {
//        sessionRepository.findBySessionNo(sessionNo)
//            .map(session -> {
//                if (!session.getUserNo().equals(userNo)) {
//                    log.warn("세션 접근 거부: requester={}, sessionNo={}", userNo, sessionNo);
//                    throw new BusinessException(ErrorCode.PERMISSION_DENIED);
//                }
//                return session;
//            })
//            .orElseThrow(() -> {
//                log.warn("세션 조회 실패 - 존재하지 않음: sessionNo={}", sessionNo);
//                return new BusinessException(ErrorCode.NOT_FOUND);
//            });
//    }
//
//    private UUID requireUser(UUID userNo) {
//        if (userNo == null) {
//            throw new BusinessException(ErrorCode.UNAUTHORIZED);
//        }
//        return userNo;
//    }
//
//    private UUID requireSession(UUID sessionNo) {
//        if (sessionNo == null) {
//            throw new BusinessException(ErrorCode.INVALID_INPUT);
//        }
//        return sessionNo;
//    }
//
//    private UUID requireMessage(UUID messageNo) {
//        if (messageNo == null) {
//            throw new BusinessException(ErrorCode.INVALID_INPUT);
//        }
//        return messageNo;
//    }
//
//    private UUID requireDocument(UUID documentNo) {
//        if (documentNo == null) {
//            throw new BusinessException(ErrorCode.INVALID_INPUT);
//        }
//        return documentNo;
//    }
//
//    private long determineNextSeq(UUID sessionNo) {
//        Pageable topOne = PageRequest.of(0, 1, Sort.by(Sort.Direction.DESC, "seq"));
//        return messageRepository.findBySessionNoOrderBySeqDesc(sessionNo, topOne).stream()
//            .map(Message::getSeq)
//            .filter(Objects::nonNull)
//            .findFirst()
//            .map(seq -> seq + 1)
//            .orElse(1L);
//    }
//
//    private List<MessageReference> mapToReferences(MessageCreateRequest request) {
//        if (request.references() == null || request.references().isEmpty()) {
//            return List.of();
//        }
//
//        return request.references().stream()
//            .map(ref -> MessageReference.builder()
//                .fileNo(ref.fileNo())
//                .name(ref.name())
//                .title(ref.title())
//                .type(ref.type())
//                .index(ref.index())
//                .downloadUrl(ref.downloadUrl())
//                .snippet(ref.snippet())
//                .build())
//            .toList();
//    }
//
//    private static MessageResponse toMessageResponse(Message chatMessage) {
//        List<ReferencedDocumentResponse> references = Optional.ofNullable(
//                chatMessage.getReferencedDocuments())
//            .orElseGet(List::of)
//            .stream()
//            .map(MessageServiceImpl::toReferencedDocumentResponse)
//            .toList();
//
//        return new MessageResponse(
//            chatMessage.getMessageNo(),
//            chatMessage.getRole(),
//            chatMessage.getUserNo(),
//            chatMessage.getLlmNo(),
//            chatMessage.getContent(),
//            chatMessage.getCreatedAt(),
//            chatMessage.getSeq(),
//            chatMessage.getInputTokens(),
//            chatMessage.getOutputTokens(),
//            chatMessage.getTotalTokens(),
//            chatMessage.getResponseTimeMs(),
//            references
//        );
//    }
//
//    private static ReferencedDocumentResponse toReferencedDocumentResponse(
//        MessageReference reference) {
//        return new ReferencedDocumentResponse(
//            reference.getFileNo(),
//            reference.getName(),
//            reference.getTitle(),
//            reference.getType(),
//            reference.getIndex(),
//            reference.getDownloadUrl(),
//            reference.getSnippet()
//        );
//    }
//
//    private static ReferencedDocumentListResponse toReferencedDocumentListResponse(
//        List<ReferencedDocumentResponse> documents
//    ) {
//        return new ReferencedDocumentListResponse(documents);
//    }
//}

