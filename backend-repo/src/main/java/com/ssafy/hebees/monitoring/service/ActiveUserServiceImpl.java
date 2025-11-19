package com.ssafy.hebees.monitoring.service;

import com.ssafy.hebees.chat.repository.SessionRepository;
import com.ssafy.hebees.common.util.MonitoringUtils;
import java.time.Duration;
import java.time.LocalDateTime;
import java.util.Set;
import java.util.UUID;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

/**
 * 활성 사용자 수 관리 서비스 구현체 Redis 기반 추적 + 채팅 세션 기반 추적 하이브리드
 */
@Slf4j
@Service
public class ActiveUserServiceImpl implements ActiveUserService {

    private static final String ACTIVE_USER_KEY_PREFIX = "active:user:";
    private static final Duration ACTIVE_TIMEOUT = Duration.ofMinutes(5);

    private final StringRedisTemplate activeUserRedisTemplate;
    private final SessionRepository sessionRepository;

    public ActiveUserServiceImpl(
        @Qualifier("activeUserRedisTemplate") StringRedisTemplate activeUserRedisTemplate,
        SessionRepository sessionRepository
    ) {
        this.activeUserRedisTemplate = activeUserRedisTemplate;
        this.sessionRepository = sessionRepository;
    }

    @Override
    public long getActiveUserCount() {
        try {
            Set<String> keys = activeUserRedisTemplate.keys(ACTIVE_USER_KEY_PREFIX + "*");
            if (keys != null) {
                keys.remove(MonitoringUtils.ACTIVE_USER_STREAM_KEY);
                return keys.size();
            }
            return 0;
        } catch (Exception e) {
            log.error("활성 사용자 수 조회 실패", e);
            return 0;
        }
    }

    @Override
    public boolean isUserActive(UUID userNo) {
        try {
            String key = ACTIVE_USER_KEY_PREFIX + userNo;
            return Boolean.TRUE.equals(activeUserRedisTemplate.hasKey(key));
        } catch (Exception e) {
            log.error("사용자 활성 상태 확인 실패: userNo={}", userNo, e);
            return false;
        }
    }
}

