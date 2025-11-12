package com.ssafy.hebees.ragsetting.dto.response;

import com.ssafy.hebees.ragsetting.entity.AgentPrompt;
import io.swagger.v3.oas.annotations.media.Schema;
import java.time.LocalDateTime;
import java.util.UUID;

@Schema(description = "에이전트 프롬프트 응답")
public record AgentPromptResponse(
    @Schema(description = "프롬프트 ID", example = "5ca5c7b9-8c3f-4c9c-9fe4-f1b9b8f5b9fe")
    UUID agentPromptNo,

    @Schema(description = "프롬프트 이름", example = "기본 상담 프롬프트")
    String name,

    @Schema(description = "프롬프트 설명", example = "기본 상담 시나리오에 사용되는 프롬프트")
    String description,

    @Schema(description = "프롬프트 내용", example = "당신은 친절한 상담원입니다...")
    String content,

    @Schema(description = "등록 일시")
    LocalDateTime createdAt,

    @Schema(description = "수정 일시")
    LocalDateTime updatedAt
) {

    public static AgentPromptResponse from(AgentPrompt agentPrompt) {
        return new AgentPromptResponse(
            agentPrompt.getAgentPromptNo(),
            agentPrompt.getName(),
            agentPrompt.getDescription(),
            agentPrompt.getContent(),
            agentPrompt.getCreatedAt(),
            agentPrompt.getUpdatedAt()
        );
    }
}

