package com.ssafy.hebees.chat.dto.request;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Positive;
import java.time.LocalDateTime;
import org.springdoc.core.annotations.ParameterObject;
import org.springframework.format.annotation.DateTimeFormat;

@ParameterObject
@Schema(description = "메시지 커서 기반 페이지 요청")
public record MessageCursorRequest(
    @Schema(description = "다음 페이지 조회를 위한 이전 커서(CREATED_AT)", nullable = true,
        type = "string", format = "date-time")
    @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
    LocalDateTime cursor,

    @Schema(description = "요청할 메시지 개수", defaultValue = "20", nullable = true)
    @Positive(message = "조회 개수는 1 이상이어야 합니다.")
    @Max(value = 100, message = "최대 100개의 메시지를 조회할 수 있습니다.")
    Integer limit
) {

    public MessageCursorRequest {
        if (limit == null) {
            limit = 20;
        }
    }
}

