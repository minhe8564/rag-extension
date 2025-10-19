package com.ssafy.hebees.common.util;

import com.ssafy.hebees.user.entity.UserRole;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;
import io.jsonwebtoken.security.Keys;
import jakarta.annotation.PostConstruct;
import jakarta.servlet.http.HttpServletRequest;
import java.security.Key;
import java.util.Date;
import java.util.UUID;
import java.util.concurrent.TimeUnit;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.StringRedisTemplate;
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

    public String generateToken(UUID userUuid, UserRole role) {
        long now = System.currentTimeMillis();
        return Jwts.builder()
            .setSubject(userUuid.toString())
            .claim("role", role)
            .setIssuedAt(new Date(now))
            .setExpiration(new Date(now + accessTokenExpiration))
            .signWith(key)
            .compact();
    }

    public String generateRefreshToken(UUID userUuid, UserRole role) {
        long now = System.currentTimeMillis();
        String refreshToken = Jwts.builder()
            .setSubject(userUuid.toString())
            .claim("role", role.name())
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
}
