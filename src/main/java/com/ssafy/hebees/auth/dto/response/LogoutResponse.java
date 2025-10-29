package com.ssafy.hebees.auth.dto.response;

import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "로그아웃 응답 DTO")
public record LogoutResponse(
    @Schema(description = "응답 메시지", example = "로그아웃이 완료되었습니다.")
    String message
) {

    public static LogoutResponse of(String message) {
        return new LogoutResponse(message);
    }
}

