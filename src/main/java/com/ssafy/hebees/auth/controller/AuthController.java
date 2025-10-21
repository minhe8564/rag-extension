package com.ssafy.hebees.auth.controller;

import com.ssafy.hebees.auth.dto.LoginRequest;
import com.ssafy.hebees.auth.dto.LoginResponse;
import com.ssafy.hebees.auth.dto.TokenRefreshRequest;
import com.ssafy.hebees.auth.dto.TokenRefreshResponse;
import com.ssafy.hebees.auth.service.AuthService;
import com.ssafy.hebees.common.util.SecurityUtil;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/auth")
@RequiredArgsConstructor
@Slf4j
@Tag(name = "인증 관리", description = "로그인, 로그아웃, 토큰 갱신 관련 API")
public class AuthController {

    private final AuthService authService;

    @PostMapping("/login")
    @Operation(summary = "로그인", description = "사용자 ID와 비밀번호로 로그인하여 JWT 토큰을 발급받습니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "로그인 성공"),
        @ApiResponse(responseCode = "400", description = "잘못된 요청 (유효성 검사 실패)"),
        @ApiResponse(responseCode = "401", description = "인증 실패 (잘못된 사용자 ID 또는 비밀번호)")
    })
    public ResponseEntity<LoginResponse> login(@Valid @RequestBody LoginRequest request) {
        log.info("로그인 요청: userId={}", request.getUserId());

        LoginResponse response = authService.login(request);

        log.info("로그인 성공: userId={}, userUuid={}", response.getUserId(), response.getUserUuid());

        return ResponseEntity.ok(response);
    }

    @PostMapping("/refresh")
    @Operation(summary = "토큰 갱신", description = "리프레시 토큰을 사용하여 새로운 액세스 토큰을 발급받습니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "토큰 갱신 성공"),
        @ApiResponse(responseCode = "400", description = "잘못된 요청"),
        @ApiResponse(responseCode = "401", description = "유효하지 않은 리프레시 토큰")
    })
    public ResponseEntity<TokenRefreshResponse> refreshToken(
        @Valid @RequestBody TokenRefreshRequest request) {
        log.info("토큰 갱신 요청");

        TokenRefreshResponse response = authService.refreshToken(request);

        log.info("토큰 갱신 성공");

        return ResponseEntity.ok(response);
    }

    @PostMapping("/logout")
    @Operation(summary = "로그아웃", description = "현재 사용자의 리프레시 토큰을 삭제하여 로그아웃합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "로그아웃 성공"),
        @ApiResponse(responseCode = "401", description = "인증되지 않은 사용자")
    })
    public ResponseEntity<Map<String, String>> logout() {
        log.info("로그아웃 요청");

        // 현재 사용자 UUID 가져오기
        String userUuid = SecurityUtil.getCurrentUserUuid()
            .orElseThrow(() -> new RuntimeException("인증되지 않은 사용자입니다."))
            .toString();

        authService.logout(userUuid);

        Map<String, String> response = new HashMap<>();
        response.put("message", "로그아웃이 완료되었습니다.");

        log.info("로그아웃 성공: userUuid={}", userUuid);

        return ResponseEntity.ok(response);
    }

    @GetMapping("/me")
    @Operation(summary = "내 정보 조회", description = "현재 로그인한 사용자의 정보를 조회합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "사용자 정보 조회 성공"),
        @ApiResponse(responseCode = "401", description = "인증되지 않은 사용자")
    })
    public ResponseEntity<Map<String, Object>> getMyInfo() {
        log.info("내 정보 조회 요청");

        String userUuid = SecurityUtil.getCurrentUserUuid()
            .orElseThrow(() -> new RuntimeException("인증되지 않은 사용자입니다."))
            .toString();

        Map<String, Object> response = new HashMap<>();
        response.put("userUuid", userUuid);
        response.put("message", "현재 로그인한 사용자 정보입니다.");

        log.info("내 정보 조회 성공: userUuid={}", userUuid);

        return ResponseEntity.ok(response);
    }

    @GetMapping("/health")
    @Operation(summary = "인증 서비스 상태 확인", description = "인증 서비스가 정상적으로 동작하는지 확인합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "서비스 정상")
    })
    public ResponseEntity<Map<String, String>> healthCheck() {
        Map<String, String> response = new HashMap<>();
        response.put("status", "UP");
        response.put("service", "Auth Service");
        response.put("timestamp", String.valueOf(System.currentTimeMillis()));

        return ResponseEntity.ok(response);
    }
}
