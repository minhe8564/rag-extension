package com.ssafy.hebees.common.util;

import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import jakarta.annotation.PostConstruct;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.Cookie;
import java.security.Key;
import java.time.Duration;
import java.util.Arrays;
import java.util.Date;
import java.util.UUID;
import java.util.concurrent.TimeUnit;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.http.ResponseCookie;
import org.springframework.stereotype.Component;

@Component
@RequiredArgsConstructor
public class JwtUtil {

    private final StringRedisTemplate redisTemplate;

    private Key key;

    @Value("${jwt.access-token-expiration}")
    private long accessTokenExpiration;

    @Value("${jwt.refresh-token-expiration}")
    private long refreshTokenExpiration;

    @Value("${jwt.secret:hebees-secret-key-for-jwt-token-generation-and-validation}")
    private String secret;

    @PostConstruct
    public void initKey() {
        this.key = Keys.hmacShaKeyFor(secret.getBytes());
    }

    public String generateToken(UUID userUuid, String roleName) {
        long now = System.currentTimeMillis();
        return Jwts.builder()
            .setSubject(userUuid.toString())
            .claim("role", roleName)
            .setIssuedAt(new Date(now))
            .setExpiration(new Date(now + accessTokenExpiration))
            .signWith(key)
            .compact();
    }

    public String generateRefreshToken(UUID userUuid, String roleName) {
        long now = System.currentTimeMillis();
        String refreshToken = Jwts.builder()
            .setSubject(userUuid.toString())
            .claim("role", roleName)
            .setIssuedAt(new Date(now))
            .setExpiration(new Date(now + refreshTokenExpiration))
            .signWith(key)
            .compact();

        // Redis에 저장
        redisTemplate.opsForValue().set(
            "refresh_token:" + userUuid,
            refreshToken,
            refreshTokenExpiration,
            TimeUnit.MILLISECONDS
        );

        return refreshToken;
    }

    public String getSubject(String token) {
        return Jwts.parserBuilder()
            .setSigningKey(key)
            .build()
            .parseClaimsJws(token)
            .getBody()
            .getSubject();
    }

    public String getRole(String token) {
        return Jwts.parserBuilder()
            .setSigningKey(key)
            .build()
            .parseClaimsJws(token)
            .getBody()
            .get("role", String.class);
    }

    public void validateToken(String token) {
        Jwts.parserBuilder()
            .setSigningKey(key)
            .build()
            .parseClaimsJws(token);
    }

    public static String extractAccessToken(HttpServletRequest request) {
        String header = request.getHeader("Authorization");
        if (header != null && header.startsWith("Bearer ")) {
            return header.substring(7);
        }
        return null;
    }

    public long getRemainingExpiration(String token) {
        return Jwts.parserBuilder()
            .setSigningKey(key)
            .build()
            .parseClaimsJws(token)
            .getBody()
            .getExpiration()
            .getTime() - System.currentTimeMillis();
    }

    /**
     * HttpOnly 쿠키 생성 (refreshToken 저장용)
     */
    public ResponseCookie createHttpOnlyRefreshCookie(String refreshToken) {
        return ResponseCookie.from("refreshToken", refreshToken)
            .httpOnly(true)
            .secure(true)
            .path("/api/v1/auth/refresh")
            .maxAge(Duration.ofDays(7))
            .sameSite("None")
            .build();
    }

    /**
     * 요청 쿠키에서 refreshToken 추출
     */
    public String extractRefreshTokenFromCookies(HttpServletRequest request) {
        if (request.getCookies() == null) return null;
        return Arrays.stream(request.getCookies())
            .filter(c -> "refreshToken".equals(c.getName()))
            .map(Cookie::getValue)
            .findFirst()
            .orElse(null);
    }

    /**
     * 입력으로 받은 토큰 문자열을 표준 형태로 정규화합니다.
     * - 앞뒤 공백 제거
     * - "Bearer " 접두사 제거
     * - 실수로 Cookie 문자열 전체가 들어온 경우 refreshToken 값만 추출
     * - 마침표가 2개를 초과하는 경우, 첫 3개 세그먼트(헤더.페이로드.서명)까지만 사용
     */
    public String normalizeToken(String token) {
        if (token == null) return null;
        String t = token.trim();

        // Remove Bearer prefix
        if (t.regionMatches(true, 0, "Bearer ", 0, 7)) {
            t = t.substring(7).trim();
        }

        // If looks like cookie header snippet, extract value after refreshToken=
        int kv = t.indexOf("refreshToken=");
        if (kv >= 0) {
            String rest = t.substring(kv + "refreshToken=".length());
            int semi = rest.indexOf(';');
            t = (semi >= 0 ? rest.substring(0, semi) : rest).trim();
        }

        // Ensure at most two dots (three JWT segments)
        int first = t.indexOf('.');
        int second = (first >= 0) ? t.indexOf('.', first + 1) : -1;
        int third = (second >= 0) ? t.indexOf('.', second + 1) : -1;
        if (third > 0) {
            t = t.substring(0, third);
        }

        return t;
    }
}
