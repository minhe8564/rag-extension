package com.ssafy.hebees.common.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;

public record PageRequest(
    @Min(value = 0, message = "페이지 번호는 0 이상이어야 합니다")
    int pageNum,

    @Min(value = 1, message = "페이지 크기는 1 이상이어야 합니다")
    @Max(value = 100, message = "페이지 크기는 100 이하여야 합니다")
    int display
) {

    public PageRequest {
        if (pageNum < 0) {
            pageNum = 0;
        }
        if (display < 1) {
            display = 10;
        }
        if (display > 100) {
            display = 100;
        }
    }

    public static PageRequest of(int pageNum, int display) {
        return new PageRequest(pageNum, display);
    }

    public static PageRequest defaultPage() {
        return new PageRequest(0, 10);
    }
}
