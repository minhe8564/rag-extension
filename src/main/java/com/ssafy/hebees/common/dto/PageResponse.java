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
        boolean first,
        boolean last
    ) {

    }

    public static <T> PageResponse<T> of(List<T> data, int pageNum, int display, long totalItems) {
        int totalPages = (int) Math.ceil((double) totalItems / display);

        PaginationInfo pagination = new PaginationInfo(
            pageNum,
            display,
            totalItems,
            totalPages,
            pageNum == 0,
            pageNum >= totalPages - 1
        );

        return new PageResponse<>(data, pagination);
    }
}
