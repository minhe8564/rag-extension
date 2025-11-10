package com.ssafy.hebees.chat.dto.request;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.Size;
import java.util.UUID;

@Schema(description = "세션 생성 DTO")
public record SessionCreateRequest(
    @Size(min = 1, max = 50, message = "제목은 1~50자여야 합니다.")
    @Schema(description = "세션 제목", example = "래그프레스 루틴", minLength = 1, maxLength = 50, nullable = true, defaultValue = "새 채팅")
    String title,

    @Schema(description = "사용할 LLM 식별자", format = "uuid", example = "bc4b6766-b861-4ad0-959b-f170767875da", nullable = true)
    UUID llm,

    @Schema(description = "사용할 LLM 이름", example = "GPT-4o", nullable = true)
    String llmName,

    @Schema(description = "초기 질문(세션명 힌트)", example = "2주뒤에 삼성전자에 가려면 오늘부터 래그프레스를 하루에 몇번씩 해야해?", nullable = true)
    String query
) {

    public static final String DEFAULT_TITLE = "새 채팅";
}




