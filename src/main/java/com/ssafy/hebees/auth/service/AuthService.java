package com.ssafy.hebees.auth.service;

import com.ssafy.hebees.auth.dto.LoginRequest;
import com.ssafy.hebees.auth.dto.LoginResponse;
import com.ssafy.hebees.auth.dto.TokenRefreshRequest;
import com.ssafy.hebees.auth.dto.TokenRefreshResponse;

public interface AuthService {

    /**
     * 사용자 로그인
     *
     * @param request 로그인 요청 정보
     * @return 로그인 응답 (토큰 포함)
     */
    LoginResponse login(LoginRequest request);

    /**
     * 토큰 갱신
     *
     * @param request 리프레시 토큰
     * @return 새로운 토큰들
     */
    TokenRefreshResponse refreshToken(TokenRefreshRequest request);

    /**
     * 로그아웃 (리프레시 토큰 삭제)
     *
     * @param userUuid 사용자 UUID
     */
    void logout(String userUuid);
}
