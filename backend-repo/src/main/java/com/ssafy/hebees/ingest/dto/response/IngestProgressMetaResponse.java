package com.ssafy.hebees.ingest.dto.response;

public record IngestProgressMetaResponse(
    String userId,
    String fileNo,
    String fileName,
    String fileCategory,
    String bucket,
    Long size,
    String status,
    String currentStep,
    Double progressPct,
    Double overallPct,
    Long createdAt,
    Long updatedAt
) {

    public static IngestProgressMetaResponse from(
        java.util.Map<?, ?> meta,
        java.util.Map<?, ?> latest
    ) {
        // Prefer values from meta; fall back to latest snapshot where appropriate
        String userId = stringValue(meta.get("userId"));
        String fileNo = stringValue(meta.get("fileNo"));
        String fileName = stringValue(meta.get("fileName"));
        String fileCategory = stringValue(meta.get("fileCategory"));
        String bucket = stringValue(meta.get("bucket"));
        Long size = parseLongOrIso(meta.get("size"));

        String status = coalesceString(meta.get("status"),
            latest == null ? null : latest.get("status"));
        String currentStep = coalesceString(meta.get("currentStep"),
            latest == null ? null : latest.get("step"));
        Double progressPct = coalesceDouble(meta.get("progressPct"),
            latest == null ? null : latest.get("progressPct"));
        Double overallPct = coalesceDouble(meta.get("overallPct"),
            latest == null ? null : latest.get("overallPct"));
        Long createdAt = parseLongOrIso(meta.get("createdAt"));
        Long updatedAt = coalesceLongOrIso(meta.get("updatedAt"),
            latest == null ? null : latest.get("ts"));

        return new IngestProgressMetaResponse(
            userId,
            fileNo,
            fileName,
            fileCategory,
            bucket,
            size,
            status,
            currentStep,
            progressPct,
            overallPct,
            createdAt,
            updatedAt
        );
    }

    private static String stringValue(Object value) {
        return value == null ? null : value.toString();
    }

    private static String coalesceString(Object a, Object b) {
        String s = stringValue(a);
        return (s != null && !s.isBlank()) ? s : stringValue(b);
    }

    private static Long parseLongOrIso(Object value) {
        if (value == null) {
            return null;
        }
        try {
            return Long.parseLong(value.toString());
        } catch (Exception e) {
            try {
                return java.time.OffsetDateTime.parse(value.toString()).toInstant().toEpochMilli();
            } catch (Exception e2) {
                try {
                    return java.time.Instant.parse(value.toString()).toEpochMilli();
                } catch (Exception e3) {
                    return null;
                }
            }
        }
    }

    private static Long coalesceLongOrIso(Object a, Object b) {
        Long x = parseLongOrIso(a);
        return x != null ? x : parseLongOrIso(b);
    }

    private static Double parseDouble(Object value) {
        try {
            return value == null ? null : Double.parseDouble(value.toString());
        } catch (Exception e) {
            return null;
        }
    }

    private static Double coalesceDouble(Object a, Object b) {
        Double x = parseDouble(a);
        return x != null ? x : parseDouble(b);
    }
}
