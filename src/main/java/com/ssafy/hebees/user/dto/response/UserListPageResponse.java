package com.ssafy.hebees.user.dto.response;

import io.swagger.v3.oas.annotations.media.Schema;
import java.util.List;

@Schema(description = "사용자 목록 페이지 응답")
public record UserListPageResponse(
    @Schema(description = "사용자 목록")
    List<UserListItemResponse> data,

    @Schema(description = "페이지네이션 정보")
    Pagination pagination
) {

    public record Pagination(
        @Schema(description = "조회할 페이지 번호(1부터)")
        int pageNum,

        @Schema(description = "페이지 당 항목 수")
        int pageSize,

        @Schema(description = "총 항목의 수")
        long totalItems,

        @Schema(description = "총 페이지의 수")
        int totalPages,

        @Schema(description = "다음 페이지 존재 여부")
        boolean hasNext
    ) {

    }

    public static UserListPageResponse of(List<UserListItemResponse> data,
        int pageNum, int pageSize, long totalItems) {
        int totalPages = (int) Math.ceil((double) totalItems / Math.max(pageSize, 1));
        boolean hasNext = pageNum < totalPages;

        return new UserListPageResponse(
            data,
            new Pagination(pageNum, pageSize, totalItems, totalPages, hasNext)
        );
    }
}

