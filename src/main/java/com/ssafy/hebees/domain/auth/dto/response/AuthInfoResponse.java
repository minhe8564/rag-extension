package com.ssafy.hebees.domain.auth.dto.response;

import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "현재 사용자 정보 응답 DTO")
public record AuthInfoResponse(
    @Schema(description = "사용자 UUID", example = "550e8400-e29b-41d4-a716-446655440000")
    String userUuid,

    @Schema(description = "응답 메시지", example = "현재 로그인한 사용자 정보입니다.")
    String message
) {

    public static AuthInfoResponse of(String userUuid, String message) {
        return new AuthInfoResponse(userUuid, message);
    }
}

