package com.ssafy.hebees.dashboard.dto.response;

import io.swagger.v3.oas.annotations.media.Schema;
import java.time.LocalDateTime;

@Schema(description = "챗봇 요청 횟수 응답 DTO")
public record ChatbotRequestCountResponse(
    @Schema(description = "응답 시각")
    LocalDateTime timestamp,

    @Schema(description = "요청 횟수")
    Integer requestCount
) {

}
