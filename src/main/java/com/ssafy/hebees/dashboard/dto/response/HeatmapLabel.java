package com.ssafy.hebees.dashboard.dto.response;

import java.util.List;
import java.util.stream.IntStream;

public record HeatmapLabel(
    List<String> days, // 요일 (7)
    List<String> slots // 시간 (24)
) {

    public static final List<String> DEFAULT_DAYS =
        List.of("월", "화", "수", "목", "금", "토", "일");

    public static final List<String> DEFAULT_SLOTS =
        IntStream.range(0, 24)
            .mapToObj(i -> String.format("%02d:00", i))
            .toList();

    public static HeatmapLabel defaults() {
        return new HeatmapLabel(DEFAULT_DAYS, DEFAULT_SLOTS);
    }
}