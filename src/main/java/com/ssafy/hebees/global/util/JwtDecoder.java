package com.ssafy.hebees.global.util;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import jakarta.annotation.PostConstruct;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.security.Key;
import java.util.Optional;
import java.util.UUID;

/**
 * JWT 토큰 디코딩 전용 유틸리티 Gateway에서 검증된 토큰을 디코딩하여 정보를 추출합니다. 서명 검증은 하지 않고 디코딩만 수행합니다.
 */
@Component
public class JwtDecoder {

    private Key key;

    @Value("${jwt.secret:hebees-secret-key-for-jwt-token-generation-and-validation}")
    private String secret;

    @PostConstruct
    public void initKey() {
        this.key = Keys.hmacShaKeyFor(secret.getBytes());
    }

    /**
     * JWT 토큰에서 사용자 UUID를 추출합니다.
     *
     * @param token JWT 토큰
     * @return 사용자 UUID, 실패 시 Optional.empty()
     */
    public Optional<UUID> extractUserUuid(String token) {
        try {
            Claims claims = getClaimsFromToken(token);
            String subject = claims.getSubject();
            return subject != null ? Optional.of(UUID.fromString(subject)) : Optional.empty();
        } catch (Exception e) {
            return Optional.empty();
        }
    }

    /**
     * JWT 토큰에서 사용자 역할명을 추출합니다.
     *
     * @param token JWT 토큰
     * @return 사용자 역할명, 실패 시 Optional.empty()
     */
    public Optional<String> extractUserRole(String token) {
        try {
            Claims claims = getClaimsFromToken(token);
            String roleClaim = claims.get("role", String.class);
            return Optional.ofNullable(roleClaim);
        } catch (Exception e) {
            return Optional.empty();
        }
    }

    /**
     * JWT 토큰에서 토큰 만료 시간을 확인합니다.
     *
     * @param token JWT 토큰
     * @return 만료 시간 (밀리초), 실패 시 0
     */
    public long getExpirationTime(String token) {
        try {
            Claims claims = getClaimsFromToken(token);
            return claims.getExpiration().getTime();
        } catch (Exception e) {
            return 0;
        }
    }

    /**
     * JWT 토큰이 만료되었는지 확인합니다.
     *
     * @param token JWT 토큰
     * @return 만료되었으면 true, 아니면 false
     */
    public boolean isTokenExpired(String token) {
        try {
            long expirationTime = getExpirationTime(token);
            return expirationTime < System.currentTimeMillis();
        } catch (Exception e) {
            return true;
        }
    }

    /**
     * JWT 토큰에서 모든 클레임을 추출합니다.
     *
     * @param token JWT 토큰
     * @return Claims 객체
     * @throws Exception 토큰 디코딩 실패 시
     */
    private Claims getClaimsFromToken(String token) throws Exception {
        return Jwts.parserBuilder()
            .setSigningKey(key)
            .build()
            .parseClaimsJws(token)
            .getBody();
    }
}
