package com.ssafy.hebees.chat.service;

import com.ssafy.hebees.chat.dto.request.MessageErrorCreateRequest;
import com.ssafy.hebees.chat.dto.request.MessageErrorSearchRequest;
import com.ssafy.hebees.chat.dto.response.MessageErrorCreateResponse;
import com.ssafy.hebees.chat.dto.response.MessageErrorResponse;
import com.ssafy.hebees.chat.entity.MessageError;
import com.ssafy.hebees.chat.entity.MessageErrorType;
import com.ssafy.hebees.chat.entity.Session;
import com.ssafy.hebees.chat.event.MessageErrorCreatedEvent;
import com.ssafy.hebees.chat.repository.MessageErrorRepository;
import com.ssafy.hebees.chat.repository.SessionRepository;
import com.ssafy.hebees.common.dto.PageRequest;
import com.ssafy.hebees.common.dto.PageResponse;
import com.ssafy.hebees.common.exception.BusinessException;
import com.ssafy.hebees.common.exception.ErrorCode;
import com.ssafy.hebees.common.util.ValidationUtil;
import com.ssafy.hebees.user.entity.User;
import com.ssafy.hebees.user.repository.UserRepository;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.UUID;
import java.util.function.Function;
import java.util.stream.Collectors;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.ApplicationEventPublisher;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Slf4j
@Service
@RequiredArgsConstructor
@Transactional
public class MessageErrorServiceImpl implements MessageErrorService {

    private final MessageErrorRepository messageErrorRepository;
    private final SessionRepository sessionRepository;
    private final UserRepository userRepository;
    private final ApplicationEventPublisher eventPublisher;

    @Override
    public MessageErrorCreateResponse createError(MessageErrorCreateRequest request) {
        UUID sessionNo = ValidationUtil.require(request.sessionNo());

        Session session = sessionRepository.findBySessionNo(sessionNo)
            .orElseThrow(() -> new BusinessException(ErrorCode.SESSION_NOT_FOUND));

        String message = ValidationUtil.require(request.message());

        MessageError error = toMessageError(request.type(), session, message);
        MessageError saved = messageErrorRepository.save(error);

        log.info("메시지 에러 로그 생성: sessionNo={}, errorNo={}",
            sessionNo, saved.getMessageErrorNo());

        eventPublisher.publishEvent(new MessageErrorCreatedEvent(saved.getType()));

        return MessageErrorCreateResponse.of(saved);
    }

    // TODO: 남겨?
    @Override
    @Transactional(readOnly = true)
    public PageResponse<MessageErrorResponse> listErrors(PageRequest pageRequest,
        MessageErrorSearchRequest searchRequest) {

        PageRequest effectivePage = pageRequest != null ? pageRequest : PageRequest.defaultPage();
        MessageErrorSearchRequest effectiveSearch = searchRequest != null
            ? searchRequest
            : new MessageErrorSearchRequest(null, null);

        Pageable pageable = org.springframework.data.domain.PageRequest.of(
            effectivePage.pageNum(),
            effectivePage.pageSize()
        );

        Page<MessageError> page = messageErrorRepository.search(
            effectiveSearch.sessionNo(),
            effectiveSearch.userNo(),
            pageable
        );

        List<MessageError> content = page.getContent().stream()
            .filter(Objects::nonNull)
            .toList();

        List<UUID> sessionIds = content.stream()
            .map(MessageError::getSessionNo)
            .filter(Objects::nonNull)
            .distinct()
            .toList();

        Map<UUID, Session> sessionsById = sessionRepository.findAllById(
                new ArrayList<>(sessionIds)).stream()
            .collect(Collectors.toMap(Session::getSessionNo, Function.identity()));

        List<UUID> userIds = content.stream()
            .map(MessageError::getUserNo)
            .filter(Objects::nonNull)
            .distinct()
            .toList();

        Map<UUID, User> usersById = userRepository.findAllById(new ArrayList<>(userIds)).stream()
            .collect(Collectors.toMap(User::getUuid, Function.identity()));

        List<MessageErrorResponse> responses = content.stream()
            .map(error -> {
                Session session = sessionsById.get(error.getSessionNo());
                User owner = usersById.get(error.getUserNo());
                return MessageErrorResponse.builder()
                    .messageErrorNo(error.getMessageErrorNo())
                    .sessionNo(error.getSessionNo())
                    .sessionTitle(
                        session == null || session.getTitle().isBlank() ? "-" : session.getTitle())
                    .userNo(error.getUserNo())
                    .userName(owner == null || owner.getName().isBlank() ? "-" : owner.getName())
                    .type(error.getType() != null ? error.getType().toValue() : "-")
                    .message(error.getMessage())
                    .build();

            })
            .toList();

        return PageResponse.of(
            responses,
            page.getNumber(),
            page.getSize(),
            page.getTotalElements()
        );
    }

    @Override
    public void deleteError(UUID errorNo) {
        ValidationUtil.require(errorNo);

        MessageError error = messageErrorRepository.findById(errorNo)
            .orElseThrow(() -> new BusinessException(ErrorCode.NOT_FOUND));

        messageErrorRepository.delete(error);
    }

    private static MessageError toMessageError(
        MessageErrorType type,
        Session session,
        String message
    ) {
        return MessageError.builder()
            .sessionNo(session.getSessionNo())
            .userNo(session.getUserNo())
            .type(type)
            .message(message)
            .build();
    }
}