package com.ssafy.hebees.chat.dto.response;

import io.swagger.v3.oas.annotations.media.Schema;
import java.util.UUID;

@Schema(description = "메시지에 포함된 참조 문서 정보")
public record ReferencedDocumentResponse(
    @Schema(description = "문서 ID", format = "uuid")
    UUID fileNo,

    @Schema(description = "파일명")
    String name,

    @Schema(description = "파일 제목")
    String title,

    @Schema(description = "파일 확장자")
    String type,

    @Schema(description = "페이지 인덱스")
    Integer index,

    @Schema(description = "문서 다운로드 URL")
    String downloadUrl,

    @Schema(description = "요약/발췌")
    String snippet
) {

}

