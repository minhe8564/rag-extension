package com.ssafy.hebees.auth.dto.request;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;

@Schema(description = "이메일로 액세스 토큰 발급 요청 DTO")
public record AccessTokenIssueByEmailRequest(
    @NotBlank
    @Email
    @Schema(description = "사용자 이메일", example = "user@example.com")
    String email
) {

}

