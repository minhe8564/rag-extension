package com.ssafy.hebees.dashboard.dto.request;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;

@Schema(description = "챗봇 스트림 스케줄링 주기 설정 요청 DTO")
public record ChatbotScheduleConfigRequest(
    @Schema(description = "스케줄링 주기 (초 단위)", example = "10")
    @NotNull(message = "intervalSeconds는 필수입니다")
    @Min(value = 1, message = "intervalSeconds는 1 이상이어야 합니다")
    Integer intervalSeconds
) {

}

