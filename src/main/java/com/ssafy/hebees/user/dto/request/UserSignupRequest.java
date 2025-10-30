package com.ssafy.hebees.user.dto.request;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.Max;

@Schema(description = "회원가입 요청 DTO")
public record UserSignupRequest(
    @NotNull(message = "이메일은 필수입니다")
    @NotBlank(message = "이메일은 필수입니다")
    @Email(message = "유효한 이메일 형식이어야 합니다")
    @Schema(description = "이메일", example = "user@example.com")
    String email,

    @NotNull(message = "비밀번호는 필수입니다")
    @NotBlank(message = "비밀번호는 필수입니다")
    @Size(min = 8, max = 20, message = "비밀번호는 8자 이상 20자 이하여야 합니다")
    @Pattern(regexp = "^(?=.*[a-zA-Z])(?=.*\\d)(?=.*[@$!%*?&])[A-Za-z\\d@$!%*?&]+$",
        message = "비밀번호는 영문, 숫자, 특수문자를 포함해야 합니다")
    @Schema(description = "비밀번호", example = "password123!")
    String password,

    @NotNull(message = "이름은 필수입니다")
    @NotBlank(message = "이름은 필수입니다")
    @Size(min = 2, max = 20, message = "이름은 2자 이상 20자 이하여야 합니다")
    @Schema(description = "이름", example = "홍길동")
    String name,

    @NotNull(message = "전화번호는 필수입니다")
    @NotBlank(message = "전화번호는 필수입니다")
    @Pattern(regexp = "^01[0-9]-\\d{3,4}-\\d{4}$", message = "유효한 전화번호 형식이어야 합니다 (예: 010-1234-5678)")
    @Schema(description = "전화번호", example = "010-1234-5678")
    String phoneNumber,

    @Min(value = 0, message = "비즈니스 타입은 0 이상이어야 합니다")
    @Max(value = 2, message = "비즈니스 타입은 2 이하여야 합니다")
    @Schema(description = "비즈니스 타입 (0: 개인 안경원, 1: 체인 안경원, 2: 제조 유통사)")
    int businessType,

    @NotNull(message = "사업자 번호는 필수입니다")
    @NotBlank(message = "사업자 번호는 필수입니다")
    @Pattern(regexp = "^\\d{3}-\\d{2}-\\d{5}$", message = "유효한 사업자 번호 형식이어야 합니다 (예: 000-00-00000)")
    @Schema(description = "사업자 번호 (OFFER_NO)", example = "123-45-67890")
    String businessNumber
) {

}

