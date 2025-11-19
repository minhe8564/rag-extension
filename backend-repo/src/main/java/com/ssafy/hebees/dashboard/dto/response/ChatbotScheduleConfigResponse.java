package com.ssafy.hebees.dashboard.dto.response;

import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "챗봇 스트림 스케줄링 주기 설정 응답 DTO")
public record ChatbotScheduleConfigResponse(
    @Schema(description = "스케줄링 주기 (초 단위)")
    Integer intervalSeconds
) {

}

