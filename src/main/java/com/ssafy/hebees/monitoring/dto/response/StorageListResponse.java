package com.ssafy.hebees.monitoring.dto.response;

import io.swagger.v3.oas.annotations.media.Schema;
import java.util.List;

@Schema(description = "스토리지 사용량 목록 응답")
public record StorageListResponse(
    @Schema(description = "데이터 기준 시각 (ISO8601)", example = "2025-11-03T18:50:00+09:00")
    String timestamp,

    @Schema(description = "파일시스템 목록", requiredMode = Schema.RequiredMode.REQUIRED)
    List<StorageInfoResponse> fileSystems
) {

}

