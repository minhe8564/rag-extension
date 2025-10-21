package com.ssafy.hebees.auth.dto;

import com.ssafy.hebees.user.entity.UserRole;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.UUID;

@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "로그인 응답 DTO")
public class LoginResponse {

    @Schema(description = "사용자 UUID", example = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")
    private UUID userUuid;

    @Schema(description = "사용자 ID", example = "ABC1234")
    private String userId;

    @Schema(description = "사용자명", example = "홍길동")
    private String userName;

    @Schema(description = "사용자 역할", example = "OPTICAL_SHOP")
    private UserRole role;

    @Schema(description = "액세스 토큰", example = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    private String accessToken;

    @Schema(description = "리프레시 토큰", example = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    private String refreshToken;

    @Schema(description = "액세스 토큰 만료 시간 (밀리초)", example = "3600000")
    private Long accessTokenExpiresIn;

    @Schema(description = "리프레시 토큰 만료 시간 (밀리초)", example = "1209600000")
    private Long refreshTokenExpiresIn;

    @Schema(description = "로그인 시간", example = "2025-10-19T16:30:00")
    private LocalDateTime loginTime;
}
