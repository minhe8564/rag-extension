package com.ssafy.hebees.auth.dto.request;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotNull;
import java.util.UUID;

@Schema(description = "액세스 토큰 발급 요청 DTO")
public record AccessTokenIssueRequest(
    @NotNull
    @Schema(description = "사용자 고유 식별자", example = "550e8400-e29b-41d4-a716-446655440000")
    UUID userNo
) {

}

