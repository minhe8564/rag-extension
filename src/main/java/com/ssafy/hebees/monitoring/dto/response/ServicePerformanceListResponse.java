package com.ssafy.hebees.monitoring.dto.response;

import io.swagger.v3.oas.annotations.media.Schema;
import java.util.List;

@Schema(description = "핵심 서비스 성능 조회 응답")
public record ServicePerformanceListResponse(
    @Schema(description = "데이터 기준 시각 (ISO8601)", example = "2025-11-03T18:35:00+09:00")
    String timestamp,

    @Schema(description = "서비스 성능 정보 목록")
    List<ServicePerformanceInfoResponse> services
) {

}
