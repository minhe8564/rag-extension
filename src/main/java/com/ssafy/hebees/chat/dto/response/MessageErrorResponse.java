package com.ssafy.hebees.chat.dto.response;

import com.fasterxml.jackson.annotation.JsonInclude;
import io.swagger.v3.oas.annotations.media.Schema;
import java.util.UUID;
import lombok.Builder;

@JsonInclude(JsonInclude.Include.NON_NULL)
@Schema(description = "메시지 에러 응답 DTO")
@Builder
public record MessageErrorResponse(
    @Schema(description = "메시지 에러 로그 ID", format = "uuid", example = "550e8400-e29b-41d4-a716-446655440000")
    UUID messageErrorNo,

    @Schema(description = "세션(채팅방) ID", format = "uuid", example = "550e8400-e29b-41d4-a716-446655440000")
    UUID sessionNo,

    @Schema(description = "세션 제목", example = "SDS 합격 비법")
    String sessionTitle,

    @Schema(description = "사용자 ID", format = "uuid", example = "550e8400-e29b-41d4-a716-446655440000")
    UUID userNo,

    @Schema(description = "사용자 이름", example = "이재원")
    String userName,

    @Schema(description = "메시지 에러 유형", example = "system")
    String type
) {

}
