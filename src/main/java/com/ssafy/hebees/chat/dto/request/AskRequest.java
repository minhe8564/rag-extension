package com.ssafy.hebees.chat.dto.request;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;

@Schema(description = "질문 요청 DTO")
public record AskRequest(
    @NotBlank(message = "질문 내용은 비어 있을 수 없습니다.")
    String content
) {

}
