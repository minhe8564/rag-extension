package com.ssafy.hebees.domain.chat.dto.response;

import io.swagger.v3.oas.annotations.media.Schema;
import java.util.List;

@Schema(description = "메시지에 포함된 참조 문서 정보")
public record ReferencedDocumentListResponse(
    @Schema(description = "문서 목록")
    List<ReferencedDocumentResponse> data
) {

}

