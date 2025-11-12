package com.ssafy.hebees.monitoring.dto.response;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Builder;

/**
 * 단일 메트릭 응답 DTO
 */
@Builder
public record MetricResponse(
    @JsonProperty("name")
    String name,

    @JsonProperty("averageTimeMs")
    Double averageTimeMs,

    @JsonProperty("count")
    Integer count,

    @JsonProperty("minTimeMs")
    Double minTimeMs,

    @JsonProperty("maxTimeMs")
    Double maxTimeMs
) {

}
