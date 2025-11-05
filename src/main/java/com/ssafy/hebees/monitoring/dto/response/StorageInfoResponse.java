package com.ssafy.hebees.monitoring.dto.response;

import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "파일시스템 스토리지 정보")
public record StorageInfoResponse(
    @Schema(description = "파일시스템 경로", example = "/")
    String path,

    @Schema(description = "총 용량(GB)", example = "200.0")
    double totalGB,

    @Schema(description = "사용 용량(GB)", example = "120.5")
    double usedGB,

    @Schema(description = "사용률 (%)", example = "60.25")
    double usagePercent
) {

}

