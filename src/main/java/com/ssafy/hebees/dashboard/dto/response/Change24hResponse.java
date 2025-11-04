package com.ssafy.hebees.dashboard.dto.response;

import io.swagger.v3.oas.annotations.media.Schema;
import java.time.LocalDateTime;

@Schema(description = "24시간 비교 응답 DTO")
public record Change24hResponse(
    Integer todayTotal, // 최근 24시간
    Integer yesterdayTotal, // 이전 24시간
    Float deltaPct, // 증갑률: (todayTotal - yesterdayTotal) / yesterdayTotal
    String direction, // 경향
    LocalDateTime asOf // 기준 시각
) {

}

