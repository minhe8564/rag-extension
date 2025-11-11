package com.ssafy.hebees.ingest.dto.response;

import java.util.List;

public record IngestProgressMetaWithStepsResponse(
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
    Long updatedAt,
    List<StepProgressResponse> steps
) {

    public static IngestProgressMetaWithStepsResponse of(
        IngestProgressMetaResponse base,
        List<StepProgressResponse> steps
    ) {
        return new IngestProgressMetaWithStepsResponse(
            base.userId(),
            base.fileNo(),
            base.fileName(),
            base.fileCategory(),
            base.bucket(),
            base.size(),
            base.status(),
            base.currentStep(),
            base.progressPct(),
            base.overallPct(),
            base.createdAt(),
            base.updatedAt(),
            steps
        );
    }
}

