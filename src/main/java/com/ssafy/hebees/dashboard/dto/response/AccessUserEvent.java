package com.ssafy.hebees.dashboard.dto.response;

public record AccessUserEvent(
    Integer accessUsers, // 일일 접속자 수
    Integer totalAccessUsers, // 전체 접속자 수
    Float deltaPct, // 증감률
    TrendDirection direction // 경향
) {

    public static AccessUserEvent of(long accessUsers, long totalAccessUsers, double deltaPct,
        TrendDirection direction) {
        return new AccessUserEvent(
            clampToInt(accessUsers),
            clampToInt(totalAccessUsers),
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
