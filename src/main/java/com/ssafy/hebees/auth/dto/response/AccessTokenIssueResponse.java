package com.ssafy.hebees.auth.dto.response;

import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "액세스 토큰 발급 응답 DTO")
public record AccessTokenIssueResponse(
    @Schema(description = "발급된 액세스 토큰", example = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    String accessToken
) {

    public static AccessTokenIssueResponse of(String accessToken) {
        return new AccessTokenIssueResponse(accessToken);
    }
}

