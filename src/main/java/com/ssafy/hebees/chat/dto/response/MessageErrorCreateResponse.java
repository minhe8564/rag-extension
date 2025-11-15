package com.ssafy.hebees.chat.dto.response;

import com.ssafy.hebees.chat.entity.MessageError;
import io.swagger.v3.oas.annotations.media.Schema;
import java.util.UUID;

@Schema(description = "메시지 에러 생성 응답 DTO")
public record MessageErrorCreateResponse(
    @Schema(description = "메시지 에러 로그 ID", format = "uuid", example = "550e8400-e29b-41d4-a716-446655440000")
    UUID messageErrorNo
) {

    public static MessageErrorCreateResponse of(MessageError messageError) {
        return new MessageErrorCreateResponse(messageError.getMessageErrorNo());
    }
}
