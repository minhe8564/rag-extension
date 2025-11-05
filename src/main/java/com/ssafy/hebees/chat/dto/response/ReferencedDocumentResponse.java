package com.ssafy.hebees.chat.dto.response;

import io.swagger.v3.oas.annotations.media.Schema;
import java.util.UUID;

@Schema(description = "메시지에 포함된 참조 문서 정보")
public record ReferencedDocumentResponse(
    @Schema(description = "문서 ID", format = "uuid", example = "3fa85f64-5717-4562-b3fc-2c963f66afa6")
    UUID fileNo,

    @Schema(description = "파일명", example = "SSAFY 부산 캠퍼스.pdf")
    String name,

    @Schema(description = "파일 제목", example = "SSAFY 부산 캠퍼스")
    String title,

    @Schema(description = "파일 확장자", example = "pdf")
    String type,

    @Schema(description = "페이지 인덱스", example = "0")
    Integer index,

    @Schema(description = "문서 다운로드 URL", example = "https://example.com/files/ssafy-busan-campus.pdf")
    String downloadUrl,

    @Schema(description = "요약/발췌", example = "부산 캠퍼스 안내 자료에서 S407 강의실 위치 및 주변 편의시설 소개.")
    String snippet
) {

}
