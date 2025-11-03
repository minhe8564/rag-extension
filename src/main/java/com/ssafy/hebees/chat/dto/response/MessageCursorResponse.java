package com.ssafy.hebees.chat.dto.response;

import io.swagger.v3.oas.annotations.media.Schema;
import java.util.List;

@Schema(description = "메시지 커서 기반 페이지 응답")
public record MessageCursorResponse(
    @Schema(description = "조회된 메시지 목록")
    List<MessageResponse> data,

    @Schema(description = "다음 페이지 요청용 커서", nullable = true)
    Long nextCursor,

    @Schema(description = "추가 데이터 존재 여부")
    boolean hasNext,

    @Schema(description = "조회한 항목의 수")
    Integer count
) {

}

