package com.ssafy.hebees.auth.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "로그인 요청 DTO")
public class LoginRequest {

    @NotBlank(message = "사용자 ID는 필수입니다")
    @Size(min = 7, max = 7, message = "사용자 ID는 7자리여야 합니다")
    @Schema(description = "사용자 ID (7자리)", example = "ABC1234")
    private String userId;

    @NotBlank(message = "비밀번호는 필수입니다")
    @Size(min = 8, max = 20, message = "비밀번호는 8자 이상 20자 이하여야 합니다")
    @Schema(description = "사용자 비밀번호", example = "password123!")
    private String password;
}
