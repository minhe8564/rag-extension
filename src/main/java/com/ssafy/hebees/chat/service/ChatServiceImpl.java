package com.ssafy.hebees.chat.service;

import com.ssafy.hebees.chat.dto.request.SessionCreateRequest;
import com.ssafy.hebees.chat.dto.request.SessionSearchRequest;
import com.ssafy.hebees.chat.dto.request.SessionUpdateRequest;
import com.ssafy.hebees.chat.dto.response.SessionCreateResponse;
import com.ssafy.hebees.chat.dto.response.SessionResponse;
import com.ssafy.hebees.chat.entity.Session;
import com.ssafy.hebees.chat.event.SessionTitleGenerationEvent;
import com.ssafy.hebees.chat.repository.SessionRepository;
import com.ssafy.hebees.common.dto.ListResponse;
import com.ssafy.hebees.common.dto.PageRequest;
import com.ssafy.hebees.common.dto.PageResponse;
import com.ssafy.hebees.common.exception.BusinessException;
import com.ssafy.hebees.common.exception.ErrorCode;
import com.ssafy.hebees.common.util.ValidationUtil;
import com.ssafy.hebees.ragsetting.entity.QueryGroup;
import com.ssafy.hebees.ragsetting.entity.Strategy;
import com.ssafy.hebees.ragsetting.repository.QueryGroupRepository;
import com.ssafy.hebees.ragsetting.repository.StrategyRepository;
import com.ssafy.hebees.user.entity.User;
import com.ssafy.hebees.user.repository.UserRepository;
import java.time.Duration;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.ApplicationEventPublisher;
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
    private final UserRepository userRepository;
    private final StrategyRepository strategyRepository;
    private final QueryGroupRepository queryGroupRepository;
    private final ApplicationEventPublisher eventPublisher;
    private final SessionTitleService sessionTitleService;

    @Override
    public ListResponse<SessionResponse> getSessions(UUID userNo, SessionSearchRequest request) {
        UUID owner = ValidationUtil.require(userNo);

        String keyword = request.query() != null ? request.query().strip() : null;

        List<Session> sessions = sessionRepository.searchSessionsByUser(owner, keyword);

        List<SessionResponse> responses = sessions.stream()
            .map(SessionResponse::of)
            .toList();

        return ListResponse.of(responses);
    }

    @Override
    public PageResponse<SessionResponse> getAllSessions(PageRequest pageRequest,
        SessionSearchRequest searchRequest) {

        Pageable pageable = org.springframework.data.domain.PageRequest.of(pageRequest.pageNum(),
            pageRequest.pageSize());
        String keyword = searchRequest.query() != null ? searchRequest.query().strip() : null;

        Page<Session> sessionPage = sessionRepository.searchAllSessions(keyword, pageable);

        List<Session> sessions = sessionPage.getContent();

        List<SessionResponse> responses = sessions.stream()
            .map(SessionResponse::of)
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
        User user = userRepository.findById(userNo)
            .orElseThrow(() -> new BusinessException(ErrorCode.USER_NOT_FOUND));
        Strategy llm = strategyRepository.findByStrategyNo(session.getLlmNo()).orElse(null);

        return SessionResponse.of(session, llm != null ? llm.getName() : "-", user.getName());
    }

    @Override
    @Transactional
    public SessionCreateResponse createSession(UUID userNo, SessionCreateRequest request) {
        String title = request.title();
        String sanitizedQuery =
            StringUtils.hasText(request.query()) ? request.query().strip() : null;
        boolean shouldAttemptTitleGeneration = false;

        if (title == null || title.isBlank()) { // 세션명이 없다면 생성
            title = SessionCreateRequest.DEFAULT_TITLE;
            if (sanitizedQuery != null) {
                shouldAttemptTitleGeneration = true;
            }
        } else {
            title = title.strip();
        }

        UUID owner = ValidationUtil.require(userNo);

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
            .build();

        Session saved = sessionRepository.save(session);
        log.info("세션 생성 성공: userNo={}, sessionNo={}", owner, saved.getSessionNo());

        String responseTitle = title;
        boolean generatedSynchronously = false;

        if (shouldAttemptTitleGeneration) {
            Optional<String> generatedTitle = generateTitleWithin(Duration.ofMillis(3000),
                sanitizedQuery);
            if (generatedTitle.isPresent()) {
                saved.updateTitle(generatedTitle.get());
                responseTitle = generatedTitle.get();
                generatedSynchronously = true;
            }
        }

        if (!generatedSynchronously && shouldAttemptTitleGeneration) {
            eventPublisher.publishEvent(
                new SessionTitleGenerationEvent(saved.getSessionNo(), sanitizedQuery));
        }

        return new SessionCreateResponse(saved.getSessionNo(), responseTitle);
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

    private Optional<String> generateTitleWithin(Duration timeout, String query) {
        if (!StringUtils.hasText(query) || timeout == null || timeout.isNegative()
            || timeout.isZero()) {
            return Optional.empty();
        }

        CompletableFuture<String> future = CompletableFuture.supplyAsync(
            () -> sessionTitleService.generate(query));

        try {
            String generated = future.get(timeout.toMillis(), TimeUnit.MILLISECONDS);
            if (StringUtils.hasText(generated)) {
                return Optional.of(generated);
            }
        } catch (TimeoutException e) {
            future.cancel(true);
            log.warn("세션 제목 동기 생성 시간이 초과되었습니다. 제한 {}초", timeout.toSeconds());
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            log.warn("세션 제목 동기 생성이 인터럽트되었습니다.");
        } catch (ExecutionException e) {
            log.warn("세션 제목 동기 생성 중 오류 발생: {}",
                e.getCause() != null ? e.getCause().getMessage() : e.getMessage());
        }

        return Optional.empty();
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
        UUID owner = ValidationUtil.require(userNo);
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

    private UUID requireSessionNo(UUID sessionNo) {
        if (sessionNo == null) {
            throw new BusinessException(ErrorCode.INPUT_NULL);
        }
        return sessionNo;
    }

    private Optional<Strategy> getDefaultLLM() {
        List<QueryGroup> llms = queryGroupRepository.findByIsDefault(true);
        if (llms == null || llms.isEmpty()) {
            return Optional.empty();
        }
        return Optional.of(llms.getFirst().getGenerationStrategy());
    }
}


