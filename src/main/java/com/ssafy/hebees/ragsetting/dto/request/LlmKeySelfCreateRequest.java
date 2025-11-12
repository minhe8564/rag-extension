package com.ssafy.hebees.ragsetting.dto.request;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.util.UUID;

@Schema(description = "사용자 LLM Key 생성 요청")
public record LlmKeySelfCreateRequest(
    @NotBlank(message = "LLM 이름은 필수입니다.")
    @Schema(description = "LLM 이름 또는 코드", requiredMode = Schema.RequiredMode.REQUIRED, example = "gpt-4o")
    String llm,

    @NotBlank(message = "API Key는 필수입니다.")
    @Size(max = 255, message = "API Key는 최대 255자까지 입력 가능합니다.")
    @Schema(description = "API Key", example = "sk-live-1234567890", requiredMode = Schema.RequiredMode.REQUIRED)
    String apiKey
) {

}


