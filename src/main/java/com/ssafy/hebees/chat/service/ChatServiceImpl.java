package com.ssafy.hebees.chat.service;

import com.ssafy.hebees.chat.dto.request.SessionCreateRequest;
import com.ssafy.hebees.chat.dto.request.SessionListRequest;
import com.ssafy.hebees.chat.dto.request.SessionUpdateRequest;
import com.ssafy.hebees.chat.dto.response.SessionCreateResponse;
import com.ssafy.hebees.chat.dto.response.SessionHistoryResponse;
import com.ssafy.hebees.chat.dto.response.SessionResponse;
import com.ssafy.hebees.chat.entity.Session;
import com.ssafy.hebees.chat.repository.SessionRepository;
import com.ssafy.hebees.common.dto.PageRequest;
import com.ssafy.hebees.common.dto.PageResponse;
import com.ssafy.hebees.common.exception.BusinessException;
import com.ssafy.hebees.common.exception.ErrorCode;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Slf4j
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class ChatServiceImpl implements ChatService {

    private final SessionRepository sessionRepository;
    private final MessageService messageService;

    @Override
    public PageResponse<SessionResponse> getSessions(UUID userNo, PageRequest pageRequest,
        SessionListRequest listRequest) {
        UUID owner = requireUser(userNo);

        Pageable pageable = org.springframework.data.domain.PageRequest.of(pageRequest.pageNum(),
            pageRequest.pageSize());
        String keyword = Optional.ofNullable(listRequest)
            .map(SessionListRequest::query)
            .orElse(null);

        Page<Session> sessionPage = sessionRepository.searchSessionsByUser(owner, keyword,
            pageable);

        List<SessionResponse> responses = sessionPage.stream()
            .map(ChatServiceImpl::toSessionResponse)
            .toList();

        return PageResponse.of(
            responses,
            sessionPage.getNumber(),
            sessionPage.getSize(),
            sessionPage.getTotalElements()
        );
    }

    @Override
    public PageResponse<SessionResponse> getAllSessions(PageRequest pageRequest,
        SessionListRequest listRequest) {
        Pageable pageable = org.springframework.data.domain.PageRequest.of(pageRequest.pageNum(),
            pageRequest.pageSize());
        String keyword = Optional.ofNullable(listRequest)
            .map(SessionListRequest::query)
            .orElse(null);

        Page<Session> sessionPage = sessionRepository.searchAllSessions(keyword, pageable);

        List<SessionResponse> responses = sessionPage.stream()
            .map(ChatServiceImpl::toSessionResponse)
            .toList();

        return PageResponse.of(
            responses,
            sessionPage.getNumber(),
            sessionPage.getSize(),
            sessionPage.getTotalElements()
        );
    }

    @Override
    public PageResponse<SessionHistoryResponse> getUserChatHistory(UUID userNo,
        PageRequest pageRequest, SessionListRequest listRequest) {
        UUID owner = requireUser(userNo);

        Pageable pageable = org.springframework.data.domain.PageRequest.of(pageRequest.pageNum(),
            pageRequest.pageSize());
        String keyword = Optional.ofNullable(listRequest)
            .map(SessionListRequest::query)
            .orElse(null);

        Page<Session> sessionPage = sessionRepository.searchSessionsByUser(owner, keyword,
            pageable);

        List<SessionHistoryResponse> responses = sessionPage.stream()
            .map(session -> new SessionHistoryResponse(
                toSessionResponse(session),
                messageService.getAllMessages(owner, session.getSessionNo())
            ))
            .toList();

        return PageResponse.of(
            responses,
            sessionPage.getNumber(),
            sessionPage.getSize(),
            sessionPage.getTotalElements()
        );
    }

    @Override
    public SessionResponse getSession(UUID userNo, UUID sessionNo) {
        Session session = getOwnedSession(userNo, sessionNo);
        return toSessionResponse(session);
    }

    @Override
    @Transactional
    public SessionCreateResponse createSession(UUID userNo, SessionCreateRequest request) {
        String title = request.title();
        if (title == null || title.isBlank()) { // 세션명이 없다면 생성
            String query = request.query();
            if (query != null) { // 사용자 질문으로 세션 제목 생성
                title = query.substring(0, 50);
            } else { // 힌트가 없다면, 기본값 사용
                title = SessionCreateRequest.DEFAULT_TITLE;
            }
        } else {
            title = title.strip();
        }

        UUID owner = requireUser(userNo);

        UUID llmNo = request.llm();
        if (llmNo == null) {
            // TODO: LLM 기본값 대체 필요
            log.warn("세션 생성 실패 - LLM 식별자 누락: userNo={}", owner);
            throw new BusinessException(ErrorCode.INVALID_INPUT);
        }

        Session session = Session.builder()
            .title(title)
            .userNo(owner)
            .llmNo(llmNo)
            .lastRequestedAt(LocalDateTime.now())
            .build();

        Session saved = sessionRepository.save(session);
        log.info("세션 생성 성공: userNo={}, sessionNo={}", owner, saved.getSessionNo());

        return new SessionCreateResponse(saved.getSessionNo(), title);
    }

    @Override
    @Transactional
    public void updateSession(UUID userNo, UUID sessionNo, SessionUpdateRequest request) {
        Session session = getOwnedSession(userNo, sessionNo);
//        session.getTitle()
        String newTitle = request.title() != null ? request.title() : "실패!";
        UUID newLlmNo = request.llm() != null ? request.llm() : session.getLlmNo();

        session.updateSettings(newTitle, newLlmNo); // TODO: LLM 유효성 검사 추가 필요
        log.info("세션 수정 요청: title={}, llmNo={}", session.getTitle(), session.getLlmNo());
        log.info("세션 수정 성공: userNo={}, sessionNo={}", session.getUserNo(), sessionNo);
    }

    @Override
    @Transactional
    public void deleteSession(UUID userNo, UUID sessionNo) {
        Session session = getOwnedSession(userNo, sessionNo);
        sessionRepository.delete(session);
        log.info("세션 삭제 성공: userNo={}, sessionNo={}", session.getUserNo(), sessionNo);
    }

    private Session getOwnedSession(UUID userNo, UUID sessionNo) {
        UUID owner = requireUser(userNo);
        UUID id = requireSessionNo(sessionNo);

        Session session = sessionRepository.findBySessionNo(id)
            .orElseThrow(() -> new BusinessException(ErrorCode.NOT_FOUND));

        if (!session.getUserNo().equals(owner)) {
            log.warn("세션 접근 거부: requester={}, owner={}, sessionNo={}", owner, session.getUserNo(),
                sessionNo);
            throw new BusinessException(ErrorCode.PERMISSION_DENIED);
        }

        return session;
    }

    private UUID requireUser(UUID userNo) {
        if (userNo == null) {
            throw new BusinessException(ErrorCode.UNAUTHORIZED);
        }
        return userNo;
    }

    private UUID requireSessionNo(UUID sessionNo) {
        if (sessionNo == null) {
            throw new BusinessException(ErrorCode.INVALID_INPUT);
        }
        return sessionNo;
    }

    private static SessionResponse toSessionResponse(Session session) {
        return new SessionResponse(
            session.getSessionNo(),
            session.getTitle(),
            session.getUpdatedAt(),
            session.getUserNo()
        );
    }
}


