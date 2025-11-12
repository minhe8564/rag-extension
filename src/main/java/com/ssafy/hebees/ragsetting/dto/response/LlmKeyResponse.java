package com.ssafy.hebees.ragsetting.dto.response;

import io.swagger.v3.oas.annotations.media.Schema;
import java.util.UUID;

@Schema(description = "LLM Key 응답")
public record LlmKeyResponse(
    @Schema(description = "LLM Key ID", example = "e3a3a951-2b44-4bd4-8c91-1d6d5f4b7a1e")
    UUID llmKeyNo,

    @Schema(description = "사용자 ID", example = "6d3efc39-d052-49a2-8d16-31a8a99f8889")
    UUID userNo,

    @Schema(description = "LLM 전략 ID", example = "1cb9d767-0a5f-4cda-9be9-7428c9af5c42")
    UUID strategyNo,

    @Schema(description = "LLM 이름", example = "GPT-4o Mini")
    String llmName,

    @Schema(description = "API Key", example = "sk-live-1234567890")
    String apiKey
) {

}


