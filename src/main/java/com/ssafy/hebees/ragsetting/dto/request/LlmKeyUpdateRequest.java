package com.ssafy.hebees.ragsetting.dto.request;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.annotation.Nullable;
import jakarta.validation.constraints.Size;
import java.util.UUID;

@Schema(description = "LLM Key 수정 요청")
public record LlmKeyUpdateRequest(
    @Schema(description = "LLM 전략 ID", nullable = true)
    @Nullable
    UUID strategyNo,

    @Schema(description = "API Key", nullable = true, example = "sk-live-1234567890")
    @Size(max = 255, message = "API Key는 최대 255자까지 입력 가능합니다.")
    @Nullable
    String apiKey
) {
}


