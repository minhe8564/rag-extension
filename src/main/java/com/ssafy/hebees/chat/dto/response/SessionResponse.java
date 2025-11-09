package com.ssafy.hebees.chat.dto.response;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonInclude.Include;
import io.swagger.v3.oas.annotations.media.Schema;
import java.time.LocalDateTime;
import java.util.UUID;

@JsonInclude(Include.NON_NULL)
@Schema(description = "세션 DTO")
public record SessionResponse(
    @Schema(description = "세션 식별자", format = "uuid", example = "550e8400-e29b-41d4-a716-446655440000")
    UUID sessionNo,

    @Schema(description = "세션 제목", example = "래그프레스 루틴")
    String title,

    @Schema(description = "세션 정보 마지막 수정 시각 (제목/설정 변경 등)", type = "string", format = "date-time", example = "2025-11-02T20:12:45")
    LocalDateTime updatedAt,

    @Schema(description = "세션이 사용 중인 LLM ID", format = "uuid", example = "f50fd9bf-984a-4d4e-b07b-f3f81febe464")
    UUID llmNo,

    @Schema(description = "세션이 사용 중인 LLM 이름", example = "gpt-4o")
    String llmName,

    @Schema(description = "사용자 ID", format = "uuid", example = "f2d5fea4b-8dcd-4e20-be92-4f96c54d8ce2")
    UUID userNo,

    @Schema(description = "사용자 이름", example = "강하늘")
    String userName
) {

}
