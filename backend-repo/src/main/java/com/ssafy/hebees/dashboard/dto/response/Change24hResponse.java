package com.ssafy.hebees.dashboard.dto.response;

import io.swagger.v3.oas.annotations.media.Schema;
import java.time.LocalDateTime;

@Schema(description = "일일 경향 응답 DTO")
public record Change24hResponse(
    Long todayTotal, // 최근 24시간
    Long yesterdayTotal, // 이전 24시간
    Float deltaPct, // 증감률 = (todayTotal - yesterdayTotal) / yesterdayTotal
    TrendDirection direction, // 경향
    LocalDateTime asOf // 기준 시각
) {

}