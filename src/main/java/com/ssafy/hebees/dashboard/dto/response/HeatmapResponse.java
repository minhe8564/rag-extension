package com.ssafy.hebees.dashboard.dto.response;

import io.swagger.v3.oas.annotations.media.Schema;
import java.util.List;

@Schema(description = "히트맵 응답 DTO")
public record HeatmapResponse(
    Timeframe timeframe,
    HeatmapLabel label,
    List<List<Integer>> cells // 사용량 매트릭스 (7x24)
) {

}

