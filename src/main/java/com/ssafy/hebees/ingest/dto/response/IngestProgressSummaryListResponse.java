package com.ssafy.hebees.ingest.dto.response;

import com.ssafy.hebees.common.dto.PageResponse;

import java.util.List;

public record IngestProgressSummaryListResponse(
    List<IngestProgressMetaWithStepsResponse> data,
    IngestProgressSummaryResponse summary,
    PageResponse.PaginationInfo pagination
) {

}

