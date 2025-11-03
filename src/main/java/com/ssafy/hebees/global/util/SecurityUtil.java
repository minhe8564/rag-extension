package com.ssafy.hebees.global.util;

import jakarta.servlet.http.HttpServletRequest;
import java.util.Optional;
import java.util.UUID;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;

@Component
public class SecurityUtil {

    private static final String JWT_TOKEN_HEADER = "X-JWT-Token";

    private static JwtDecoder jwtDecoder;

    @Autowired
    public void setJwtDecoder(JwtDecoder jwtDecoder) {
        SecurityUtil.jwtDecoder = jwtDecoder;
    }

    /**
     * 현재 사용자의 UUID를 반환합니다. Gateway에서 전달된 JWT 토큰을 디코딩하여 사용자 정보를 추출합니다.
     *
     * @return 사용자 UUID가 있으면 Optional.of(UUID), 없으면 Optional.empty()
     */
    public static Optional<UUID> getCurrentUserUuid() {
        String token = getJwtTokenFromRequest();
        if (token != null && jwtDecoder != null) {
            return jwtDecoder.extractUserUuid(token);
        }
        return Optional.empty();
    }

    /**
     * 현재 사용자의 역할명을 반환합니다. Gateway에서 전달된 JWT 토큰을 디코딩하여 사용자 역할을 추출합니다.
     *
     * @return 사용자 역할명이 있으면 Optional.of(String), 없으면 Optional.empty()
     */
    public static Optional<String> getCurrentUserRole() {
        String token = getJwtTokenFromRequest();
        if (token != null && jwtDecoder != null) {
            return jwtDecoder.extractUserRole(token);
        }
        return Optional.empty();
    }

    /**
     * 현재 HTTP 요청에서 JWT 토큰을 추출합니다. 1. X-JWT-Token 헤더 확인 (Gateway를 통한 요청) 2. Authorization Bearer 헤더
     * 확인 (직접 요청)
     *
     * @return JWT 토큰, 없으면 null
     */
    private static String getJwtTokenFromRequest() {
        try {
            ServletRequestAttributes attributes = (ServletRequestAttributes) RequestContextHolder.getRequestAttributes();
            if (attributes != null) {
                HttpServletRequest request = attributes.getRequest();

                String jwtToken = request.getHeader(JWT_TOKEN_HEADER);
                if (jwtToken != null) {
                    return jwtToken;
                }

                String authHeader = request.getHeader("Authorization");
                if (authHeader != null && authHeader.startsWith("Bearer ")) {
                    return authHeader.substring(7);
                }
            }
        } catch (Exception e) {

        }
        return null;
    }
}
