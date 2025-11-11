package com.ssafy.hebees.ragsetting.dto.request;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.util.UUID;

@Schema(description = "LLM Key 생성 요청")
public record LlmKeyCreateRequest(
    @NotNull(message = "사용자 ID는 필수입니다.")
    @Schema(description = "사용자 ID", requiredMode = Schema.RequiredMode.REQUIRED)
    UUID userNo,

    @NotNull(message = "전략 ID는 필수입니다.")
    @Schema(description = "LLM 전략 ID", requiredMode = Schema.RequiredMode.REQUIRED)
    UUID strategyNo,

    @NotBlank(message = "API Key는 필수입니다.")
    @Size(max = 255, message = "API Key는 최대 255자까지 입력 가능합니다.")
    @Schema(description = "API Key", example = "sk-live-1234567890", requiredMode = Schema.RequiredMode.REQUIRED)
    String apiKey
) {
}


