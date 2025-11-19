package com.ssafy.hebees.dashboard.dto.response;

import io.swagger.v3.oas.annotations.media.Schema;
import java.time.LocalDateTime;

@Schema(description = "총 에러 수 응답 DTO")
public record TotalErrorsResponse(
    Long totalErrors, // 총 에러 수
    LocalDateTime asOf // 기준 시각
) {

    public static TotalErrorsResponse of(Long totalErrors, LocalDateTime asOf) {
        return new TotalErrorsResponse(totalErrors, asOf);
    }

}

