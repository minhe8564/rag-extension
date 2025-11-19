package com.ssafy.hebees.user.dto.response;

import com.ssafy.hebees.user.entity.User;
import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "사용자 정보 응답 DTO")
public record UserInfoResponse(
    @Schema(description = "사용자 ID", example = "550e8400-e29b-41d4-a716-446655440000")
    String userNo,

    @Schema(description = "이메일", example = "owner@glasseslab.co.kr")
    String email,

    @Schema(description = "이름", example = "김사장")
    String name,

    @Schema(description = "권한(모드)", example = "1")
    Integer role,

    @Schema(description = "소속 사업자 번호", example = "1234567890")
    String offerNo,

    @Schema(description = "소속 사업체 유형", example = "1")
    Integer businessType
) {

    public static UserInfoResponse of(User user) {
        return new UserInfoResponse(
            user.getUuid() != null ? user.getUuid().toString() : null,
            user.getEmail(),
            user.getName(),
            user.getUserRole() != null ? user.getUserRole().getMode() : null,
            user.getOffer() != null ? user.getOffer().getOfferNo() : null,
            user.getBusinessType()
        );
    }
}

