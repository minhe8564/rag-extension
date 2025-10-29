package com.ssafy.hebees.auth.dto.request;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

@Schema(description = "토큰 갱신 요청 DTO")
public record TokenRefreshRequest(
    @NotNull(message = "리프레시 토큰은 필수입니다")
    @NotBlank(message = "리프레시 토큰은 필수입니다")
    @Schema(description = "리프레시 토큰", example = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    String refreshToken
) {

}
