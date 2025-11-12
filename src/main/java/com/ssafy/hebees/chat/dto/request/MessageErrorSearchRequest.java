package com.ssafy.hebees.chat.dto.request;

import io.swagger.v3.oas.annotations.media.Schema;
import java.util.UUID;
import org.springdoc.core.annotations.ParameterObject;

@ParameterObject
@Schema(description = "메시지 에러 검색 요청 DTO")
public record MessageErrorSearchRequest(
    @Schema(description = "조회할 세션(채팅방) ID", format = "uuid", nullable = true)
    UUID sessionNo,

    @Schema(description = "조회할 사용자 ID", format = "uuid", nullable = true)
    UUID userNo
) {

}
