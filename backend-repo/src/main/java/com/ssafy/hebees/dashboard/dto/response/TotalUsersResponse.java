package com.ssafy.hebees.dashboard.dto.response;

import io.swagger.v3.oas.annotations.media.Schema;
import java.time.LocalDateTime;

@Schema(description = "총 접속자 수 응답 DTO")
public record TotalUsersResponse(
    Long totalUser, // 총 접속자 수
    LocalDateTime asOf // 기준 시각
) {

    public static TotalUsersResponse of(Long totalUser, LocalDateTime asOf) {
        return new TotalUsersResponse(totalUser, asOf);
    }

}

