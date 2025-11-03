package com.ssafy.hebees.global.dto;

import java.util.List;

public record PageResponse<T>(
    List<T> data,
    PaginationInfo pagination
) {

    public record PaginationInfo(
        int pageNum,
        int display,
        long totalItems,
        int totalPages,
        boolean first,
        boolean last,
        boolean hasNext
    ) {

    }

    public static <T> PageResponse<T> of(List<T> data, int pageNum, int pageSize, long totalItems) {
        int totalPages = (int) Math.ceil((double) totalItems / pageSize);

        PaginationInfo pagination = new PaginationInfo(
            pageNum,
            pageSize,
            totalItems,
            totalPages,
            pageNum == 0,
            pageNum >= totalPages - 1,
            pageNum < totalPages - 1
        );

        return new PageResponse<>(data, pagination);
    }
}
