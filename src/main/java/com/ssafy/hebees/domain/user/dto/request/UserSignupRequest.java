package com.ssafy.hebees.domain.user.dto.request;

// 회원가입 요청 DTO

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
    @Email(message = "유효한 이메일 형식이 아닙니다")
    @Schema(description = "이메일", example = "user@example.com")
    String email,

    @NotNull(message = "비밀번호는 필수입니다")
    @NotBlank(message = "비밀번호는 필수입니다")
    @Size(min = 8, max = 20, message = "비밀번호는 8자 이상 20자 이하여야 합니다")
    @Pattern(regexp = "^(?=.*[a-zA-Z])(?=.*\\d)(?=.*[@$!%*?&])[A-Za-z\\d@$!%*?&]+$",
        message = "비밀번호는 영문, 숫자, 특수문자를 포함해야 합니다")
    @Schema(description = "비밀번호", example = "Str0ngP@ssw0rd!")
    String password,

    @NotNull(message = "이름은 필수입니다")
    @NotBlank(message = "이름은 필수입니다")
    @Size(min = 2, max = 20, message = "이름은 2자 이상 20자 이하여야 합니다")
    @Schema(description = "이름", example = "이재모 안경원")
    String name,

    @Min(value = 0, message = "비즈니스 타입은 0 이상이어야 합니다")
    @Max(value = 2, message = "비즈니스 타입은 2 이하여야 합니다")
    @Schema(description = "비즈니스 타입(0: 개인 안경원, 1: 체인 안경원, 2: 제조 유통사)")
    int businessType,

    @NotNull(message = "사업자 번호는 필수입니다")
    @NotBlank(message = "사업자 번호는 필수입니다")
    @Pattern(regexp = "^\\d{10}$", message = "사업자 번호는 하이픈 없는 10자리 숫자여야 합니다(예: 1234567890)")
    @Schema(description = "사업자번호 (OFFER_NO)", example = "1234567890")
    String offerNo
) {

}
