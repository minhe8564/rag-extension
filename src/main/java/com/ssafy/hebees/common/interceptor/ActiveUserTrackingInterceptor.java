package com.ssafy.hebees.common.interceptor;

import com.ssafy.hebees.common.util.MonitoringUtils;
import com.ssafy.hebees.common.util.RedisStreamUtils;
import com.ssafy.hebees.common.util.SecurityUtil;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.time.Duration;
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

/**
 * 활성 사용자 추적 Interceptor 모든 API 요청에서 인증된 사용자의 활동을 Redis Stream에 기록
 */
@Slf4j
@Component
public class ActiveUserTrackingInterceptor implements HandlerInterceptor {

    private static final String ACTIVE_USER_KEY_PREFIX = "active:user:";
    private static final Duration ACTIVE_TIMEOUT = Duration.ofMinutes(5);
    private static final String ADMIN_ROLE = "ADMIN";
    private static final String ADMIN_AUTHORITY = "ROLE_ADMIN";
    private static final long STREAM_MAX_LENGTH = 1000; // Stream 최대 길이

    private final StringRedisTemplate activeUserRedisTemplate;

    public ActiveUserTrackingInterceptor(
        @Qualifier("activeUserRedisTemplate") StringRedisTemplate activeUserRedisTemplate
    ) {
        this.activeUserRedisTemplate = activeUserRedisTemplate;
        log.info("ActiveUserTrackingInterceptor 초기화 완료. Redis Template: {}",
            activeUserRedisTemplate != null ? "주입됨" : "null");
    }

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response,
        Object handler) {
        String path = request.getRequestURI();

        // 인증된 사용자만 추적
        Optional<UUID> userNo = SecurityUtil.getCurrentUserUuid();
        Optional<String> userRole = SecurityUtil.getCurrentUserRole().map(String::trim);

        // 관리자는 Redis에 추가하지 않음
        if (isAdminUser(userRole)) {
            log.debug("인터셉터 스킵: 관리자 사용자는 추적하지 않음. userNo={}, role={}, path={}",
                userNo.orElse(null), userRole.orElse("UNKNOWN"), path);
            return true;
        }

        if (userNo.isPresent() && isApiRequest(request)) {
            try {
                String userUuidStr = userNo.get().toString();
                String key = ACTIVE_USER_KEY_PREFIX + userUuidStr;

                // Key-Value로 TTL 관리 (활성 사용자 수 조회용)
                activeUserRedisTemplate.opsForValue().set(key, "1", ACTIVE_TIMEOUT);

                // Redis Stream에 이벤트 추가 (SSE 스트리밍용)
                Map<String, String> streamRecord = new HashMap<>();
                streamRecord.put("userUuid", userUuidStr);
                streamRecord.put("timestamp", String.valueOf(System.currentTimeMillis()));
                streamRecord.put("path", path);

                String recordId = RedisStreamUtils.addRecord(
                    activeUserRedisTemplate,
                    MonitoringUtils.ACTIVE_USER_STREAM_KEY,
                    streamRecord
                );

                // Stream 크기 제한 (최근 1000개만 유지)
                RedisStreamUtils.trimStream(
                    activeUserRedisTemplate,
                    MonitoringUtils.ACTIVE_USER_STREAM_KEY,
                    STREAM_MAX_LENGTH,
                    true
                );

                log.debug("활성 사용자 추적 성공: userNo={}, path={}, streamId={}",
                    userNo.get(), path, recordId);

            } catch (Exception e) {
                log.error("활성 사용자 추적 실패: userNo={}, path={}, error={}",
                    userNo.get(), path, e.getMessage(), e);
            }
        } else {
            if (!userNo.isPresent()) {
                log.debug("인터셉터 스킵: 사용자 UUID 없음, path={}", path);
            } else if (!isApiRequest(request)) {
                log.debug("인터셉터 스킵: API 요청 아님, path={}", path);
            }
        }

        return true;
    }

    private boolean isAdminUser(Optional<String> userRole) {
        if (userRole.isPresent() && ADMIN_ROLE.equalsIgnoreCase(userRole.get())) {
            return true;
        }

        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        if (authentication != null && authentication.getAuthorities() != null) {
            for (GrantedAuthority authority : authentication.getAuthorities()) {
                if (ADMIN_AUTHORITY.equalsIgnoreCase(authority.getAuthority())) {
                    return true;
                }
            }
        }
        return false;
    }

    /**
     * API 요청인지 확인 Actuator, Swagger, 정적 리소스는 제외
     */
    private boolean isApiRequest(HttpServletRequest request) {
        String path = request.getRequestURI();

        // API 경로가 아니면 제외
        if (!path.startsWith("/api/v1")) {
            return false;
        }

        // Actuator, Swagger, 정적 리소스 제외
        if (path.contains("/actuator") ||
            path.contains("/swagger") ||
            path.contains("/v3/api-docs")) {
            return false;
        }

        return true;
    }
}
