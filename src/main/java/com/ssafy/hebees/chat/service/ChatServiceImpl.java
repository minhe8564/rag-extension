package com.ssafy.hebees.chat.service;

import com.ssafy.hebees.chat.client.RunpodClient;
import com.ssafy.hebees.chat.client.dto.RunpodChatMessage;
import com.ssafy.hebees.chat.client.dto.RunpodChatResult;
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
import com.ssafy.hebees.ragsetting.entity.QueryGroup;
import com.ssafy.hebees.ragsetting.entity.Strategy;
import com.ssafy.hebees.ragsetting.repository.QueryGroupRepository;
import com.ssafy.hebees.ragsetting.repository.StrategyRepository;
import com.ssafy.hebees.user.entity.User;
import com.ssafy.hebees.user.repository.UserRepository;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;
import java.util.stream.Collectors;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

@Slf4j
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class ChatServiceImpl implements ChatService {

    private final SessionRepository sessionRepository;
    private final MessageService messageService;
    private final RunpodClient runpodClient;
    private final UserRepository userRepository;
    private final StrategyRepository strategyRepository;
    private final QueryGroupRepository queryGroupRepository;

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

        List<Session> sessions = sessionPage.getContent();

        List<SessionResponse> responses = sessions.stream()
            .map(this::toSessionResponse)
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

        List<Session> sessions = sessionPage.getContent();
        Map<UUID, String> userNames = resolveUserNames(sessions);

        List<SessionResponse> responses = sessions.stream()
            .map(this::toSessionResponse)
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

        List<Session> sessions = sessionPage.getContent();

        List<SessionHistoryResponse> responses = sessions.stream()
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
        Map<UUID, String> userNames = resolveUserNames(List.of(session));
        Strategy llm = strategyRepository.findByStrategyNo(session.getLlmNo()).orElse(null);
        return toSessionResponse(session,
            llm != null ? llm.getName() : "-",
            userNames.get(session.getUserNo())
        );
    }

    @Override
    @Transactional
    public SessionCreateResponse createSession(UUID userNo, SessionCreateRequest request) {
        LocalDateTime lastRequestedAt = null;

        String title = request.title();
        if (title == null || title.isBlank()) { // 세션명이 없다면 생성
            String query = request.query();
            if (StringUtils.hasText(query)) { // 사용자 질문으로 세션 제목 생성
                title = generateSessionTitle(query);
                lastRequestedAt = LocalDateTime.now();
            } else { // 힌트가 없다면, 기본값 사용
                title = SessionCreateRequest.DEFAULT_TITLE;
            }
        } else {
            title = title.strip();
        }

        UUID owner = requireUser(userNo);

        String llmInput = request.llm();
        UUID llmNo;
        if (StringUtils.hasText(llmInput)) {
            llmNo = resolveLlmNo(llmInput);
        } else { // LLM 기본값 사용
            llmNo = getDefaultLLM().orElseThrow(
                () -> new BusinessException(ErrorCode.INTERNAL_SERVER_ERROR)
            ).getStrategyNo();
        }

        Session session = Session.builder()
            .title(title)
            .userNo(owner)
            .llmNo(llmNo)
            .lastRequestedAt(lastRequestedAt)
            .build();

        Session saved = sessionRepository.save(session);
        log.info("세션 생성 성공: userNo={}, sessionNo={}", owner, saved.getSessionNo());

        return new SessionCreateResponse(saved.getSessionNo(), title);
    }

    private UUID resolveLlmNo(String identifier) {
        String trimmed = identifier != null ? identifier.strip() : null;
        if (!StringUtils.hasText(trimmed)) {
            throw new BusinessException(ErrorCode.BAD_REQUEST);
        }

        try {
            UUID candidate = UUID.fromString(trimmed);
            return strategyRepository.findByStrategyNo(candidate)
                .map(Strategy::getStrategyNo)
                .orElseThrow(() -> new BusinessException(ErrorCode.BAD_REQUEST));
        } catch (IllegalArgumentException ignored) {
            return strategyRepository.findByNameAndCodeStartingWith(trimmed, "GEN")
                .orElseThrow(() -> new BusinessException(ErrorCode.BAD_REQUEST))
                .getStrategyNo();
        }
    }

    @Override
    public String generateSessionTitle(String query) {
        String sanitizedQuery = query.strip();
        if (!StringUtils.hasText(sanitizedQuery)) {
            return SessionCreateRequest.DEFAULT_TITLE;
        }

        try {
            RunpodChatResult result = runpodClient.chat(List.of(
                RunpodChatMessage.of("system",
                    "You are an assistant that reads the user's question and replies only with a concise Korean session title under 15   characters. Do not include punctuation or any extra text."),
                RunpodChatMessage.of("user", sanitizedQuery)
            ));

            String title = Optional.ofNullable(result)
                .map(RunpodChatResult::content)
                .map(String::trim)
                .orElse("");

            if (!StringUtils.hasText(title)) {
                return fallbackTitle(sanitizedQuery);
            }

            if (title.length() > 20) {
                title = title.substring(0, 20);
            }

            return title;
        } catch (BusinessException e) {
            log.warn("Runpod 세션 제목 생성 실패: {}", e.getMessage());
            return fallbackTitle(sanitizedQuery);
        } catch (Exception e) {
            log.error("Runpod 세션 제목 생성 중 알 수 없는 오류", e);
            return fallbackTitle(sanitizedQuery);
        }
    }

    private String fallbackTitle(String query) {
        String candidate = query.length() > 20 ? query.substring(0, 20) : query;
        return StringUtils.hasText(candidate) ? candidate : SessionCreateRequest.DEFAULT_TITLE;
    }

    @Override
    @Transactional
    public void updateSession(UUID userNo, UUID sessionNo, SessionUpdateRequest request) {
        Session session = getOwnedSession(userNo, sessionNo);
        String newTitle = request.title() != null ? request.title() : session.getTitle();

        UUID newLlmNo;
        if (StringUtils.hasText(request.llm())) {
            newLlmNo = resolveLlmNo(request.llm());
        } else {
            newLlmNo = session.getLlmNo();
        }

        session.updateSettings(newTitle, newLlmNo);
        log.info("세션 수정 요청: title={}, llm={}", request.title(), request.llm());
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

    private Map<UUID, String> resolveUserNames(List<Session> sessions) {
        if (sessions == null || sessions.isEmpty()) {
            return Map.of();
        }

        Set<UUID> userIds = sessions.stream()
            .map(Session::getUserNo)
            .filter(Objects::nonNull)
            .collect(Collectors.toSet());

        if (userIds.isEmpty()) {
            return Map.of();
        }

        return userRepository.findAllById(userIds).stream()
            .filter(user -> user.getName() != null)
            .collect(Collectors.toMap(User::getUuid, User::getName, (first, second) -> first));
    }

    private SessionResponse toSessionResponse(Session session) {
        return toSessionResponse(session, null, null);
    }

    private SessionResponse toSessionResponse(Session session, String llmName, String userName) {
        return new SessionResponse(
            session.getSessionNo(),
            session.getTitle(),
            session.getUpdatedAt(),
            session.getLlmNo(),
            llmName,
            session.getUserNo(),
            userName
        );
    }

    private Optional<Strategy> getDefaultLLM() {
        List<QueryGroup> llms = queryGroupRepository.findByIsDefault(true);
        if (llms == null || llms.isEmpty()) {
            return Optional.empty();
        }
        return Optional.of(llms.getFirst().getGenerationStrategy());
    }
}


