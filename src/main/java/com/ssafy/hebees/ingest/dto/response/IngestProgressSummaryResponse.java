package com.ssafy.hebees.ingest.dto.response;

public record IngestProgressSummaryResponse(
    int completed,
    int total
) {

}
