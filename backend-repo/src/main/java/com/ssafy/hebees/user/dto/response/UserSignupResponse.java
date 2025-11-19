package com.ssafy.hebees.user.dto.response;

import com.ssafy.hebees.user.entity.User;
import io.swagger.v3.oas.annotations.media.Schema;

import java.time.LocalDateTime;
import java.util.UUID;

@Schema(description = "회원가입 응답 DTO")
public record UserSignupResponse(
    @Schema(description = "사용자 UUID", example = "123e4567-e89b-12d3-a456-426614174000")
    UUID userUuid,

    @Schema(description = "사용자 이메일", example = "user@example.com")
    String email,

    @Schema(description = "사용자 이름", example = "홍길동")
    String name,

    @Schema(description = "사용자 역할명", example = "ADMIN")
    String roleName,

    @Schema(description = "비즈니스 타입", example = "개인 안경원")
    int businessType,

    @Schema(description = "가입일시", example = "2024-01-01T12:00:00")
    LocalDateTime createdAt
) {

    /**
     * 사용자 정보로 UserSignupResponse 생성
     */
    public static UserSignupResponse of(User user) {
        return new UserSignupResponse(
            user.getUuid(),
            user.getEmail(),
            user.getName(),
            user.getRoleName(),
            user.getBusinessType(),
            user.getCreatedAt()
        );
    }
}
