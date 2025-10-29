package com.ssafy.hebees.auth.dto.response;

import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "인증 서비스 상태 응답 DTO")
public record AuthHealthResponse(
    @Schema(description = "서비스 상태", example = "UP")
    String status,

    @Schema(description = "서비스명", example = "Auth Service")
    String service,

    @Schema(description = "타임스탬프", example = "1700000000000")
    String timestamp
) {

    public static AuthHealthResponse of(String status, String service, String timestamp) {
        return new AuthHealthResponse(status, service, timestamp);
    }
}

