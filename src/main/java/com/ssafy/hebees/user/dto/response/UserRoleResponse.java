package com.ssafy.hebees.user.dto.response;

import com.ssafy.hebees.user.entity.UserRole;
import io.swagger.v3.oas.annotations.media.Schema;

import java.util.UUID;

@Schema(description = "사용자 역할 응답 DTO")
public record UserRoleResponse(
    @Schema(description = "사용자 역할 UUID", example = "123e4567-e89b-12d3-a456-426614174000")
    UUID uuid,

    @Schema(description = "모드", example = "1")
    Integer mode,

    @Schema(description = "이름", example = "ADMIN")
    String name
) {

    public static UserRoleResponse from(UserRole userRole) {
        return new UserRoleResponse(
            userRole.getUuid(),
            userRole.getMode(),
            userRole.getName()
        );
    }
}

