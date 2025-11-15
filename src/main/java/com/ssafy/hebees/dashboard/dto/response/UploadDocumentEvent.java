package com.ssafy.hebees.dashboard.dto.response;

public record UploadDocumentEvent(
    Integer uploadedDocs, // 일일 업로드 문서 수
    Integer totalUploadedDocs, // 전체 업로드 문서 수
    Float deltaPct, // 증감률
    TrendDirection direction // 경향
) {

    public static UploadDocumentEvent of(long uploadedDocs, long totalUploadedDocs,
        double deltaPct, TrendDirection direction) {
        return new UploadDocumentEvent(
            clampToInt(uploadedDocs),
            clampToInt(totalUploadedDocs),
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
