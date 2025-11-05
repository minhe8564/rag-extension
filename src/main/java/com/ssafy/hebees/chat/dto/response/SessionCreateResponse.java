package com.ssafy.hebees.chat.dto.response;

import io.swagger.v3.oas.annotations.media.Schema;
import java.util.UUID;

@Schema(name = "SessionCreateResponse", description = "세션 생성 결과")
public record SessionCreateResponse(
    @Schema(description = "생성된 세션 ID", format = "uuid", example = "550e8400-e29b-41d4-a716-446655440000")
    UUID sessionNo,
    @Schema(description = "세션명", example = "래그프레스를 매일 했더니 삼전에 갔습니다")
    String title
) {

}
