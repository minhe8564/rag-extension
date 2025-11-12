package com.ssafy.hebees.common.dto;

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
            pageNum < totalPages - 1
        );

        return new PageResponse<>(data, pagination);
    }
}
