package com.ssafy.hebees.ragsetting.dto.request;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

@Schema(description = "에이전트 프롬프트 수정 요청")
public record AgentPromptUpdateRequest(
    @NotBlank(message = "프롬프트 이름은 필수입니다.")
    @Size(max = 100, message = "프롬프트 이름은 최대 100자까지 입력 가능합니다.")
    @Schema(description = "프롬프트 이름", example = "기본 상담 프롬프트", requiredMode = Schema.RequiredMode.REQUIRED)
    String name,

    @Size(max = 255, message = "설명은 최대 255자까지 입력 가능합니다.")
    @Schema(description = "프롬프트 설명", example = "갱신된 상담 프롬프트 설명")
    String description,

    @NotBlank(message = "프롬프트 내용은 필수입니다.")
    @Schema(description = "프롬프트 내용", example = "상담 응답 시 고객의 감정을 고려하세요...")
    String content
) {

}

