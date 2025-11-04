package com.ssafy.hebees.monitoring.dto.response;

import io.swagger.v3.oas.annotations.media.Schema;
import java.util.List;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Schema(description = "핵심 서비스 성능 조회 응답")
@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ServicePerformanceListResponse {

    @Schema(description = "데이터 기준 시각 (ISO8601)", example = "2025-11-03T18:35:00+09:00")
    private String timestamp;

    @Schema(description = "서비스 성능 정보 목록")
    private List<ServicePerformanceInfoResponse> services;
}
