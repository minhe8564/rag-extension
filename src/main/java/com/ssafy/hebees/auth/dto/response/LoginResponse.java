package com.ssafy.hebees.auth.dto.response;

import com.ssafy.hebees.user.entity.User;
import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "로그인 응답 DTO")
public record LoginResponse(
    @Schema(description = "사용자명", example = "홍길동")
    String name,

    @Schema(description = "사용자 역할명", example = "ADMIN")
    String roleName,

    @Schema(description = "비즈니스 타입", example = "개인 안경원")
    String businessType,

    @Schema(description = "액세스 토큰", example = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    String accessToken,

    @Schema(description = "리프레시 토큰", example = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    String refreshToken
) {

    /**
     * 사용자 정보와 토큰으로 LoginResponse 생성
     */
    public static LoginResponse of(User user, String accessToken, String refreshToken) {
        return new LoginResponse(
            user.getName(),
            user.getRoleName(),
            user.getBusinessType(),
            accessToken,
            refreshToken
        );
    }
}
