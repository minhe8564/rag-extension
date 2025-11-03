package com.ssafy.hebees.common.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import org.springdoc.core.annotations.ParameterObject;

@ParameterObject
@Schema(description = "오프셋 기반 페이지네이션 쿼리 파라미터 (0-based pageNum)")
public record PageRequest(

        @Schema(description = "페이지 번호 (0부터 시작하는 오프셋 인덱스)", example = "0", minimum = "0", defaultValue = "0")
        @Min(value = 0, message = "페이지 번호는 0 이상이어야 합니다")
        int pageNum,

        @Schema(description = "페이지 크기(한 페이지 항목 수)", example = "10", minimum = "1", maximum = "100", defaultValue = "10")
        @Min(value = 1, message = "페이지 크기는 1 이상이어야 합니다")
        @Max(value = 100, message = "페이지 크기는 100 이하여야 합니다")
        int pageSize
) {

    public PageRequest {
        if (pageNum < 0) {
            pageNum = 0;
        }
        if (pageSize < 1) {
            pageSize = 10;
        }
        if (pageSize > 100) {
            pageSize = 100;
        }
    }

    public static PageRequest of(int pageNum, int pageSize) {
        return new PageRequest(pageNum, pageSize);
    }

    @Schema(hidden = true)
    public static PageRequest defaultPage() {
        return new PageRequest(0, 10);
    }
}
