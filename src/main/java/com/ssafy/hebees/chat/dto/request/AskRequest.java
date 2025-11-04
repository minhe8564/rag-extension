package com.ssafy.hebees.chat.dto.request;

import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "질문 요청 DTO")
public record AskRequest(
    String content
) {

}
