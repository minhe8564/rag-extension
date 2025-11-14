package com.ssafy.hebees.chat.dto.request;

import com.ssafy.hebees.chat.entity.MessageErrorType;
import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.util.UUID;

@Schema(description = "메시지 에러 생성 요청 DTO")
public record MessageErrorCreateRequest(
    @Schema(description = "메시지 에러 유형", example = "SYSTEM")
    @NotNull(message = "에러 유형은 필수입니다.")
    MessageErrorType type,

    @Schema(description = "에러가 발생한 세션(채팅방) ID", format = "uuid", example = "550e8400-e29b-41d4-a716-446655440000")
    @NotNull(message = "세션 ID는 필수입니다.")
    UUID sessionNo,

    @Schema(description = "에러 상세 메시지", example = "LLM 응답 생성에 실패했습니다.")
    @NotBlank(message = "에러 메시지를 입력해주세요.")
    @Size(max = 1023, message = "에러 메시지는 1023자를 초과할 수 없습니다.")
    String message
) {

    public MessageErrorCreateRequest {
        message = sanitizeMessage(message());
    }

    private String sanitizeMessage(String message) {
        if (message == null) {
            return "-";
        }
        String trimmed = message.strip();
        return trimmed.isEmpty() ? "-" : trimmed;
    }
}
