package com.ssafy.hebees.user.dto;

import com.ssafy.hebees.user.entity.UserRole;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.UUID;

@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "회원가입 응답 DTO")
public class UserSignupResponse {

    @Schema(description = "사용자 UUID", example = "123e4567-e89b-12d3-a456-426614174000")
    private UUID userUuid;

    @Schema(description = "사용자 이메일", example = "user@example.com")
    private String email;

    @Schema(description = "사용자 이름", example = "홍길동")
    private String name;

    @Schema(description = "사용자 역할", example = "OPTICAL_SHOP")
    private UserRole role;

    @Schema(description = "회사명", example = "안경점 ABC")
    private String companyName;

    @Schema(description = "가입일시", example = "2024-01-01T12:00:00")
    private LocalDateTime createdAt;
}
