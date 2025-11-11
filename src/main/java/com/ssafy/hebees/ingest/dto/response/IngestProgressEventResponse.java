package com.ssafy.hebees.ingest.dto.response;

public record IngestProgressEventResponse(
    String eventType,
    String userId,
    String fileNo,
    String currentStep,
    String status,
    Integer processed,
    Integer total,
    Double progressPct,
    Double overallPct,
    Long ts
) {

    public static IngestProgressEventResponse fromMaps(
        java.util.Map<?, ?> meta,
        java.util.Map<?, ?> fields,
        java.util.UUID userUuid,
        String defaultEventType
    ) {
        String userId = stringValue(
            coalesce(meta.get("userId"), userUuid == null ? null : userUuid.toString()));
        String fileNo = stringValue(meta.get("fileNo"));
        String currentStep = stringValue(coalesce(
            coalesce(fields.get("currentStep"), fields.get("step")),
            meta.get("currentStep")));
        String status = stringValue(coalesce(fields.get("status"), meta.get("status")));
        Integer processed = parseInt(coalesce(fields.get("processed"), meta.get("processed")));
        Integer total = parseInt(coalesce(fields.get("total"), meta.get("total")));
        Double progressPct = parseDouble(
            coalesce(fields.get("progressPct"), meta.get("progressPct")));
        Double overallPct = parseDouble(coalesce(fields.get("overallPct"), meta.get("overallPct")));
        Long ts = parseLong(coalesce(fields.get("ts"), meta.get("updatedAt")));

        String eventType = stringValue(coalesce(fields.get("eventType"), defaultEventType));
        if (eventType == null || eventType.isBlank()) {
            // Derive from status when possible
            if (status != null) {
                String s = status.toUpperCase();
                if ("COMPLETED".equals(s)) {
                    eventType = "RUN_COMPLETED";
                } else if ("FAILED".equals(s)) {
                    eventType = "RUN_FAILED";
                }
            }
            if (eventType == null || eventType.isBlank()) {
                eventType = "STEP_UPDATE";
            }
        }

        return new IngestProgressEventResponse(
            eventType,
            userId,
            fileNo,
            currentStep,
            status,
            processed,
            total,
            progressPct,
            overallPct,
            ts
        );
    }

    private static Object coalesce(Object a, Object b) {
        return a != null ? a : b;
    }

    private static String stringValue(Object value) {
        return value == null ? null : value.toString();
    }

    private static Integer parseInt(Object value) {
        try {
            return value == null ? null : Integer.parseInt(value.toString());
        } catch (Exception e) {
            return null;
        }
    }

    private static Long parseLong(Object value) {
        try {
            return value == null ? null : Long.parseLong(value.toString());
        } catch (Exception e) {
            return null;
        }
    }

    private static Double parseDouble(Object value) {
        try {
            return value == null ? null : Double.parseDouble(value.toString());
        } catch (Exception e) {
            return null;
        }
    }
}
