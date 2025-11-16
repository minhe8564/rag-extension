package com.ssafy.hebees.llmKey.dto.request;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

@Schema(description = "사용자 LLM Key 생성 요청")
public record LlmKeyCreateRequest(
    @NotBlank(message = "LLM 이름은 필수입니다.")
    @Schema(description = "LLM 이름 또는 ID", example = "gpt-4o 또는 1cb9d767-0a5f-4cda-9be9-7428c9af5c42")
    String llm,

    @NotBlank(message = "API Key는 필수입니다.")
    @Size(max = 255, message = "API Key는 최대 255자까지 입력 가능합니다.")
    @Schema(description = "API Key", example = "sk-live-1234567890")
    String apiKey
) {

}
