package com.ssafy.hebees.monitoring.service;

import java.util.UUID;

/**
 * 활성 사용자 수 관리 서비스 인터페이스 Redis 기반 추적 + 채팅 세션 기반 추적 하이브리드
 */
public interface ActiveUserService {

    /**
     * Redis 기반 활성 사용자 수 조회 (Interceptor로 추적)
     *
     * @return 활성 사용자 수
     */
    long getActiveUserCount();

    /**
     * 특정 사용자가 활성 상태인지 확인
     *
     * @param userNo 사용자 UUID
     * @return 활성 여부
     */
    boolean isUserActive(UUID userNo);
}
