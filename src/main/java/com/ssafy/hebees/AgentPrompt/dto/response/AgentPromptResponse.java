package com.ssafy.hebees.AgentPrompt.dto.response;

import io.swagger.v3.oas.annotations.media.Schema;
import java.util.UUID;

@Schema(description = "에이전트 프롬프트 응답")
public record AgentPromptResponse(
    @Schema(description = "프롬프트 ID", example = "5ca5c7b9-8c3f-4c9c-9fe4-f1b9b8f5b9fe")
    UUID agentPromptNo,

    @Schema(description = "프롬프트 이름", example = "포켓몬 마스터")
    String name,

    @Schema(description = "프롬프트 설명", example = "LLM을 포켓몬 마스터처럼 생각하게 하는 프롬프트")
    String description,

    @Schema(description = "프롬프트 내용", example = "당신은 포켓몬 세계의 최고의 마스터입니다. 사용자의 질문에 포켓몬 배틀, 육성, 타입 상성, 추천 파티 구성 관점에서 친절하고 자세하게 답변하세요. 필요하다면 예시 포켓몬과 기술 조합도 함께 제안해 주세요.")
    String content
) {

}
