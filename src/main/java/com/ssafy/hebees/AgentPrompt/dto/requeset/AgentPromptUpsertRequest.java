package com.ssafy.hebees.AgentPrompt.dto.requeset;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

@Schema(description = "에이전트 프롬프트 생성 요청")
public record AgentPromptUpsertRequest(
    @NotBlank(message = "프롬프트 이름은 필수입니다.")
    @Size(max = 100, message = "프롬프트 이름은 최대 100자까지 입력 가능합니다.")
    @Schema(description = "프롬프트 이름", example = "포켓몬 마스터", requiredMode = Schema.RequiredMode.REQUIRED)
    String name,

    @Size(max = 255, message = "설명은 최대 255자까지 입력 가능합니다.")
    @Schema(description = "프롬프트 설명", example = "LLM을 포켓몬 마스터처럼 생각하게 하는 프롬프트")
    String description,

    @NotBlank(message = "프롬프트 내용은 필수입니다.")
    @Schema(description = "프롬프트 내용", example = "당신은 포켓몬 세계의 최고의 마스터입니다. 사용자의 질문에 포켓몬 배틀, 육성, 타입 상성, 추천 파티 구성 관점에서 친절하고 자세하게 답변하세요. 필요하다면 예시 포켓몬과 기술 조합도 함께 제안해 주세요.")
    String content
) {

}
