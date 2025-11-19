package com.ssafy.hebees.ingest.dto.response;

public record IngestNotificationSummaryResponse(
    int total,
    int completed,
    int successCount,
    int failedCount
) {

}

