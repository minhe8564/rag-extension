package com.ssafy.hebees.chat.dto.response;

import io.swagger.v3.oas.annotations.media.Schema;
import java.time.LocalDateTime;

@Schema(description = "질문 응답 DTO")
public record AskResponse(
    String content,
    LocalDateTime timestamp
) {

}
