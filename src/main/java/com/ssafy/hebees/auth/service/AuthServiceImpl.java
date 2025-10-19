package com.ssafy.hebees.auth.service;

import com.ssafy.hebees.auth.dto.LoginRequest;
import com.ssafy.hebees.auth.dto.LoginResponse;
import com.ssafy.hebees.auth.dto.TokenRefreshRequest;
import com.ssafy.hebees.auth.dto.TokenRefreshResponse;
import com.ssafy.hebees.common.exception.BusinessException;
import com.ssafy.hebees.common.exception.ErrorCode;
import com.ssafy.hebees.common.util.JwtUtil;
import com.ssafy.hebees.user.entity.User;
import com.ssafy.hebees.user.service.UserService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.UUID;
import java.util.concurrent.TimeUnit;

@Slf4j
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class AuthServiceImpl implements AuthService {

    private final UserService userService;
    private final PasswordEncoder passwordEncoder;
    private final JwtUtil jwtUtil;
    private final StringRedisTemplate redisTemplate;

    @Value("${jwt.access-token-expiration}")
    private long accessTokenExpiration;

    @Value("${jwt.refresh-token-expiration}")
    private long refreshTokenExpiration;

    @Override
    @Transactional
    public LoginResponse login(LoginRequest request) {
        log.info("로그인 시도: userId={}", request.getUserId());

        // 사용자 조회
        User user = userService.findByUserId(request.getUserId());

        // 비밀번호 검증
        if (!passwordEncoder.matches(request.getPassword(), user.getPassword())) {
            log.warn("로그인 실패: 비밀번호 불일치 - userId={}", request.getUserId());
            throw new BusinessException(ErrorCode.INVALID_SIGNIN);
        }

        // JWT 토큰 생성
        String accessToken = jwtUtil.generateToken(user.getUuid(), user.getRole());
        String refreshToken = jwtUtil.generateRefreshToken(user.getUuid(), user.getRole());

        log.info("로그인 성공: userId={}, userUuid={}", user.getUserId(), user.getUuid());

        return LoginResponse.builder()
            .userUuid(user.getUuid())
            .userId(user.getUserId())
            .userName(user.getUserName())
            .role(user.getRole())
            .accessToken(accessToken)
            .refreshToken(refreshToken)
            .accessTokenExpiresIn(accessTokenExpiration)
            .refreshTokenExpiresIn(refreshTokenExpiration)
            .loginTime(LocalDateTime.now())
            .build();
    }

    @Override
    @Transactional
    public TokenRefreshResponse refreshToken(TokenRefreshRequest request) {
        log.info("토큰 갱신 시도");

        try {
            // 리프레시 토큰 검증
            jwtUtil.validateToken(request.getRefreshToken());

            // 토큰에서 사용자 정보 추출
            String userUuidStr = jwtUtil.getSubject(request.getRefreshToken());
            UUID userUuid = UUID.fromString(userUuidStr);

            // Redis에서 리프레시 토큰 확인
            String storedRefreshToken = redisTemplate.opsForValue()
                .get("refresh_token:" + userUuid);
            if (storedRefreshToken == null || !storedRefreshToken.equals(
                request.getRefreshToken())) {
                log.warn("토큰 갱신 실패: 유효하지 않은 리프레시 토큰");
                throw new BusinessException(ErrorCode.INVALID_REFRESH_TOKEN);
            }

            // 사용자 정보 조회
            User user = userService.findByUuid(userUuid);

            // 새로운 토큰 생성
            String newAccessToken = jwtUtil.generateToken(user.getUuid(), user.getRole());
            String newRefreshToken = jwtUtil.generateRefreshToken(user.getUuid(), user.getRole());

            log.info("토큰 갱신 성공: userUuid={}", userUuid);

            return TokenRefreshResponse.builder()
                .accessToken(newAccessToken)
                .refreshToken(newRefreshToken)
                .accessTokenExpiresIn(accessTokenExpiration)
                .refreshTokenExpiresIn(refreshTokenExpiration)
                .build();

        } catch (Exception e) {
            log.warn("토큰 갱신 실패: {}", e.getMessage());
            throw new BusinessException(ErrorCode.INVALID_REFRESH_TOKEN);
        }
    }

    @Override
    @Transactional
    public void logout(String userUuid) {
        log.info("로그아웃: userUuid={}", userUuid);

        // Redis에서 리프레시 토큰 삭제
        redisTemplate.delete("refresh_token:" + userUuid);

        log.info("로그아웃 완료: userUuid={}", userUuid);
    }
}
