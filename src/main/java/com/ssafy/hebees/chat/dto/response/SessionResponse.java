package com.ssafy.hebees.chat.dto.response;

import io.swagger.v3.oas.annotations.media.Schema;

import java.time.LocalDateTime;
import java.util.UUID;

@Schema(description = "세션 DTO")
public record SessionResponse(
    @Schema(description = "세션 식별자", format = "uuid", example = "550e8400-e29b-41d4-a716-446655440000")
    UUID sessionNo,

    @Schema(description = "세션 제목", example = "래그프레스 루틴")
    String title,

    @Schema(description = "세션 생성 시각", type = "string", format = "date-time", example = "2025-11-02T20:10:30")
    LocalDateTime createdAt,

    @Schema(description = "세션 정보 마지막 수정 시각 (제목/설정 변경 등)", type = "string", format = "date-time", example = "2025-11-02T20:12:45")
    LocalDateTime updatedAt,

    @Schema(description = "세션의 마지막 활동 시각 (조회/메시지 전송 등 사용자 요청 기준)", type = "string", format = "date-time", example = "2025-11-02T20:15:00")
    LocalDateTime lastRequestedAt
) { }
