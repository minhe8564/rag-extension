package com.ssafy.hebees.dashboard.dto.response;

public record ErrorEvent(
    Integer errorCount, // 일일 에러 수
    Integer totalError, // 전체 에러 수
    Float deltaPct, // 증감률
    TrendDirection direction // 경향
) {

    public static ErrorEvent of(long errorCount, long totalError, double deltaPct,
        TrendDirection direction) {
        return new ErrorEvent(
            clampToInt(errorCount),
            clampToInt(totalError),
            (float) deltaPct,
            direction
        );
    }

    private static int clampToInt(long value) {
        if (value > Integer.MAX_VALUE) {
            return Integer.MAX_VALUE;
        }
        if (value < Integer.MIN_VALUE) {
            return Integer.MIN_VALUE;
        }
        return (int) value;
    }
}
