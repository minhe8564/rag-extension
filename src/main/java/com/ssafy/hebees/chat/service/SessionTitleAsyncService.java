package com.ssafy.hebees.chat.service;

import com.ssafy.hebees.chat.dto.request.SessionCreateRequest;
import com.ssafy.hebees.chat.entity.Session;
import com.ssafy.hebees.chat.repository.SessionRepository;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

@Slf4j
@Service
@RequiredArgsConstructor
public class SessionTitleAsyncService {

    private final SessionRepository sessionRepository;
    private final SessionTitleService sessionTitleService;

    @Async
    @Transactional
    public void generateSessionTitle(UUID sessionNo, String query) {
        if (!StringUtils.hasText(query)) {
            return;
        }
        log.info("세션 제목 생성 시작: sessionNo={}, query={}", sessionNo, query);
        try {
            var sessionOptional = sessionRepository.findBySessionNo(sessionNo);
            if (sessionOptional.isEmpty()) {
                log.warn("세션 제목 비동기 생성 중 세션 없음: sessionNo={}", sessionNo);
                return;
            }

            Session session = sessionOptional.get();
            if (!SessionCreateRequest.DEFAULT_TITLE.equals(session.getTitle())) {
                return;
            }

            String generatedTitle = sessionTitleService.generate(query);
            if (StringUtils.hasText(generatedTitle)
                && !generatedTitle.equals(session.getTitle())) {
                session.updateTitle(generatedTitle);
                log.info("세션 제목 비동기 업데이트 성공: sessionNo={}", sessionNo);
            }
        } catch (Exception e) {
            log.error("세션 제목 비동기 생성 실패: sessionNo={}", sessionNo, e);
        }
    }
}

