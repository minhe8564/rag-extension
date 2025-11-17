package com.ssafy.hebees.chat.dto.response;

import com.fasterxml.jackson.annotation.JsonInclude;
import io.swagger.v3.oas.annotations.media.Schema;
import java.time.LocalDateTime;
import java.util.UUID;

@JsonInclude(JsonInclude.Include.NON_NULL)
@Schema(description = "질문 스트리밍 초기 응답 DTO")
public record AskStreamInitResponse(
    @Schema(description = "생성된 메시지 식별자", example = "2f1b9af4-3e6d-4a2c-8b7a-123456789abc", format = "uuid")
    UUID messageNo,
    @Schema(description = "메시지 역할", example = "ai")
    String role,
    @Schema(description = "응답이 생성된 시각")
    LocalDateTime createdAt
) {

    public static AskStreamInitResponse from(AskResponse response) {
        if (response == null) {
            return new AskStreamInitResponse(null, null, null);
        }
        return new AskStreamInitResponse(
            response.messageNo(),
            response.role(),
            response.createdAt()
        );
    }
}

