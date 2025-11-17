package com.ssafy.hebees.notification.dto.response;

import io.swagger.v3.oas.annotations.media.Schema;
import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;
import lombok.Builder;

@Schema(description = "알림 커서 기반 페이지 응답")
public record NotificationCursorResponse(
    @Schema(description = "조회된 알림 목록")
    List<NotificationItemResponse> data,

    Pagination pagination
) {

    @Schema(description = "알림 항목")
    @Builder(toBuilder = true)
    public record NotificationItemResponse(
        @Schema(description = "알림 ID", format = "uuid")
        UUID notificationNo,

        @Schema(description = "알림 카테고리", example = "INGEST")
        String category,

        @Schema(description = "이벤트 타입", example = "INGEST_SUMMARY_COMPLETED")
        String eventType,

        @Schema(description = "참조 ID", example = "redis-stream-id")
        String referenceId,

        @Schema(description = "알림 제목")
        String title,

        @Schema(description = "총 작업 수")
        int total,

        @Schema(description = "성공 수")
        int successCount,

        @Schema(description = "실패 수")
        int failedCount,

        @Schema(description = "읽음 여부")
        boolean isRead,

        @Schema(description = "생성 시각", type = "string", format = "date-time")
        LocalDateTime createdAt
    ) {

    }

    public record Pagination(
        @Schema(description = "추가 데이터 존재 여부")
        boolean hasNext,

        @Schema(description = "다음 페이지 요청용 커서", nullable = true, type = "string",
            format = "date-time")
        LocalDateTime nextCursor,

        @Schema(description = "조회한 항목의 수")
        Integer count
    ) {

    }
}

