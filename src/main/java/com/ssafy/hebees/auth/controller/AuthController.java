package com.ssafy.hebees.auth.controller;

import com.ssafy.hebees.auth.dto.request.LoginRequest;
import com.ssafy.hebees.auth.dto.request.TokenRefreshRequest;
import com.ssafy.hebees.auth.dto.response.AuthHealthResponse;
import com.ssafy.hebees.auth.dto.response.LoginResponse;
import com.ssafy.hebees.auth.dto.response.LogoutResponse;
import com.ssafy.hebees.auth.dto.response.TokenRefreshResponse;
import com.ssafy.hebees.auth.service.AuthService;
import com.ssafy.hebees.common.response.BaseResponse;
import com.ssafy.hebees.common.util.SecurityUtil;
import com.ssafy.hebees.common.util.JwtUtil;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.ResponseCookie;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

@RestController
@RequestMapping("/auth")
@RequiredArgsConstructor
@Slf4j
@Tag(name = "인증 API", description = "로그인/로그아웃/토큰 API")
@Validated
public class AuthController {

    private final AuthService authService;
    private final JwtUtil jwtUtil;

    @PostMapping("/login")
    @Operation(summary = "로그인")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "로그인 성공")
    })
    public ResponseEntity<BaseResponse<LoginResponse>> login(
        @Valid @RequestBody LoginRequest request,
        HttpServletResponse servletResponse) {
        log.info("login request: email={}", request.email());
        LoginResponse response = authService.login(request);
        // 로그인 시 발급된 refreshToken을 HttpOnly 쿠키로 세팅 (JwtUtil 사용)
        try {
            ResponseCookie refreshTokenCookie = jwtUtil.createHttpOnlyRefreshCookie(
                response.refreshToken());
            servletResponse.setHeader(HttpHeaders.SET_COOKIE, refreshTokenCookie.toString());
        } catch (Exception e) {
            log.warn("Failed to set refresh token cookie: {}", e.getMessage());
        }
        // 본문에는 refreshToken이 직렬화되지 않도록 처리됨(@JsonIgnore)
        return ResponseEntity.ok(BaseResponse.success(response));
    }

    @PostMapping("/refresh")
    @Operation(summary = "토큰 재발급")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "재발급 성공")
    })
    public ResponseEntity<BaseResponse<TokenRefreshResponse>> refreshToken(
        HttpServletRequest servletRequest,
        HttpServletResponse servletResponse) {

        // 1) 쿠키에서 refreshToken 우선 추출
        String refreshTokenFromCookie = jwtUtil.extractRefreshTokenFromCookies(servletRequest);

        if (refreshTokenFromCookie == null || refreshTokenFromCookie.isBlank()) {
            log.warn("refreshToken not provided in cookie or body");
            return ResponseEntity.badRequest().body(
                BaseResponse.error(org.springframework.http.HttpStatus.BAD_REQUEST,
                    "BAD_REQUEST",
                    "refreshToken is required",
                    null)
            );
        }

        String normalized = jwtUtil.normalizeToken(refreshTokenFromCookie);
        TokenRefreshResponse response = authService.refreshToken(
            new TokenRefreshRequest(normalized));

        // 3) 새 refreshToken을 쿠키로 갱신
        try {
            ResponseCookie refreshTokenCookie = jwtUtil.createHttpOnlyRefreshCookie(
                response.refreshToken());
            servletResponse.setHeader(HttpHeaders.SET_COOKIE, refreshTokenCookie.toString());
        } catch (Exception e) {
            log.warn("Failed to update refresh token cookie: {}", e.getMessage());
        }

        return ResponseEntity.ok(BaseResponse.success(response));
    }

    @PostMapping("/logout")
    @Operation(summary = "로그아웃")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "로그아웃 성공")
    })
    public ResponseEntity<BaseResponse<LogoutResponse>> logout() {
        var userUuid = SecurityUtil.getCurrentUserUuid()
            .orElseThrow(() -> new RuntimeException("인증된 사용자가 없습니다."))
            .toString();
        authService.logout(userUuid);
        return ResponseEntity.ok(BaseResponse.success(LogoutResponse.of("로그아웃되었습니다.")));
    }

    @GetMapping("/health")
    @Operation(summary = "상태 확인")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "UP")
    })
    public ResponseEntity<BaseResponse<AuthHealthResponse>> healthCheck() {
        String timestamp = String.valueOf(System.currentTimeMillis());
        return ResponseEntity.ok(
            BaseResponse.success(AuthHealthResponse.of("UP", "Auth Service", timestamp)));
    }
}
