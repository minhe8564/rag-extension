package com.ssafy.hebees.domain.user.dto.response;

import com.ssafy.hebees.domain.user.entity.User;
import io.swagger.v3.oas.annotations.media.Schema;

import java.time.LocalDateTime;
import java.util.UUID;

@Schema(description = "사용자 응답 DTO")
public record UserResponse(
    @Schema(description = "사용자 UUID", example = "123e4567-e89b-12d3-a456-426614174000")
    UUID uuid,

    @Schema(description = "이메일", example = "user@example.com")
    String email,

    @Schema(description = "이름", example = "홍길동")
    String name,

    @Schema(description = "역할명", example = "USER")
    String roleName,

    @Schema(description = "사업자 번호", example = "1234567890")
    String offerNo,

    @Schema(description = "비즈니스 타입 (0: 개인, 1: 체인, 2: 제조/유통)", example = "0")
    int businessType,

    @Schema(description = "생성일시", example = "2024-01-01T12:00:00")
    LocalDateTime createdAt,

    @Schema(description = "수정일시", example = "2024-01-01T12:00:00")
    LocalDateTime updatedAt
) {

    /**
     * User 엔티티로부터 UserResponse 생성
     */
    public static UserResponse from(User user) {
        return new UserResponse(
            user.getUuid(),
            user.getEmail(),
            user.getName(),
            user.getRoleName(),
            user.getOffer() != null ? user.getOffer().getOfferNo() : null,
            user.getBusinessType(),
            user.getCreatedAt(),
            user.getUpdatedAt()
        );
    }
}

