package com.ssafy.hebees.chat.dto.response;

import io.swagger.v3.oas.annotations.media.Schema;
import java.util.List;

@Schema(description = "세션과 메시지 내역 응답")
public record SessionHistoryResponse(
    @Schema(description = "세션 정보", requiredMode = Schema.RequiredMode.REQUIRED)
    SessionResponse session,

    @Schema(description = "세션에 속한 메시지 목록", requiredMode = Schema.RequiredMode.REQUIRED)
    List<MessageResponse> messages
) {

}

