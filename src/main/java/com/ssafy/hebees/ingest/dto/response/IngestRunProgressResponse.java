package com.ssafy.hebees.ingest.dto.response;

public record IngestRunProgressResponse(
    String id,
    String type,
    Long runId,
    Long docId,
    String docName,
    String step,
    Integer processed,
    Integer total,
    Double progressPct,
    Double overallPct,
    String status,
    Long ts
) {

    public static IngestRunProgressResponse from(
        org.springframework.data.redis.connection.stream.MapRecord<String, ?, ?> record) {
        java.util.Map<?, ?> fields = record.getValue();
        return new IngestRunProgressResponse(
            record.getId().getValue(),
            stringValue(fields.get("type")),
            parseLong(fields.get("runId")),
            parseLong(fields.get("docId")),
            stringValue(fields.get("docName")),
            stringValue(fields.get("step")),
            parseInt(fields.get("processed")),
            parseInt(fields.get("total")),
            parseDouble(fields.get("progressPct")),
            parseDouble(fields.get("overallPct")),
            stringValue(fields.get("status")),
            parseLong(fields.get("ts"))
        );
    }

    /**
     * Build response from a stream record while overriding meta values (runId, docId, docName).
     */
    public static IngestRunProgressResponse fromRecordWithMeta(
        org.springframework.data.redis.connection.stream.MapRecord<String, ?, ?> record,
        String runId,
        Object docId,
        Object docName
    ) {
        java.util.Map<?, ?> fields = record.getValue();
        return new IngestRunProgressResponse(
            record.getId().getValue(),
            "run_progress",
            parseLong(runId),
            parseLong(docId),
            stringValue(docName),
            stringValue(fields.get("step")),
            parseInt(fields.get("processed")),
            parseInt(fields.get("total")),
            parseDouble(fields.get("progressPct")),
            parseDouble(fields.get("overallPct")),
            stringValue(fields.get("status")),
            parseLong(fields.get("ts"))
        );
    }

    /**
     * Build response from the latest snapshot hash and supplemental info.
     */
    public static IngestRunProgressResponse fromLatestSnapshot(
        String runId,
        Object docId,
        Object docName,
        java.util.Map<?, ?> latest,
        String id
    ) {
        return new IngestRunProgressResponse(
            id,
            "run_progress",
            parseLong(runId),
            parseLong(docId),
            stringValue(docName),
            stringValue(latest.get("step")),
            parseInt(latest.get("processed")),
            parseInt(latest.get("total")),
            parseDouble(latest.get("progressPct")),
            parseDouble(latest.get("overallPct")),
            stringValue(latest.get("status")),
            parseLong(latest.get("ts"))
        );
    }

    private static Long parseLong(Object value) {
        try {
            return value == null ? null : Long.parseLong(value.toString());
        } catch (NumberFormatException e) {
            return null;
        }
    }

    private static Integer parseInt(Object value) {
        try {
            return value == null ? null : Integer.parseInt(value.toString());
        } catch (NumberFormatException e) {
            return null;
        }
    }

    private static Double parseDouble(Object value) {
        try {
            return value == null ? null : Double.parseDouble(value.toString());
        } catch (NumberFormatException e) {
            return null;
        }
    }

    private static String stringValue(Object value) {
        return value == null ? null : value.toString();
    }
}
