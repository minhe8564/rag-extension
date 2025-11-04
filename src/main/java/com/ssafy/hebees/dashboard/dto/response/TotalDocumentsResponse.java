package com.ssafy.hebees.dashboard.dto.response;

import io.swagger.v3.oas.annotations.media.Schema;
import java.time.LocalDateTime;

@Schema(description = "총 문서 수 응답 DTO")
public record TotalDocumentsResponse(
    Integer totalDocs, // 총 업로드 문서 수
    LocalDateTime asOf // 기준 시각
) {

    public static TotalDocumentsResponse of(Integer totalDocs, LocalDateTime asOf) {
        return new TotalDocumentsResponse(
            totalDocs,
            asOf
        );
    }

}

