package com.ssafy.hebees.dashboard.dto.response;

import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "챗봇 스트림 난수값 설정 응답 DTO")
public record ChatbotRandomConfigResponse(
    @Schema(description = "난수값 포함 활성화 여부")
    Boolean enabled,

    @Schema(description = "난수값 하한 (lower)")
    Integer lower,

    @Schema(description = "난수값 상한 (upper)")
    Integer upper
) {

}

