package com.ssafy.hebees.monitoring.dto.response;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

/**
 * 메트릭 목록 응답 DTO
 */
public record MetricsListResponse(
    @JsonProperty("metrics")
    List<MetricResponse> metrics
) {

}
