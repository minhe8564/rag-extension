package com.ssafy.hebees.dashboard.dto.request;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.Min;

@Schema(description = "챗봇 스트림 난수값 설정 요청 DTO")
public record ChatbotRandomConfigRequest(
    @Schema(description = "난수값 포함 활성화 여부")
    Boolean enabled,

    @Schema(description = "난수값 하한 (lower)")
    @Min(value = 0, message = "lower는 0 이상이어야 합니다")
    Integer lower,

    @Schema(description = "난수값 상한 (upper)")
    @Min(value = 0, message = "upper는 0 이상이어야 합니다")
    Integer upper
) {

}

