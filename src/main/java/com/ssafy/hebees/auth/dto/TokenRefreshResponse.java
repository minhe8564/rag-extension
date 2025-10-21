package com.ssafy.hebees.auth.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "토큰 갱신 응답 DTO")
public class TokenRefreshResponse {

    @Schema(description = "새로운 액세스 토큰", example = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    private String accessToken;

    @Schema(description = "새로운 리프레시 토큰", example = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    private String refreshToken;

    @Schema(description = "액세스 토큰 만료 시간 (밀리초)", example = "3600000")
    private Long accessTokenExpiresIn;

    @Schema(description = "리프레시 토큰 만료 시간 (밀리초)", example = "1209600000")
    private Long refreshTokenExpiresIn;
}
