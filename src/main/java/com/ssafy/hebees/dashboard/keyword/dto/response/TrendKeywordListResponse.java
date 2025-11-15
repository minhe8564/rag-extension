package com.ssafy.hebees.dashboard.keyword.dto.response;

import com.ssafy.hebees.dashboard.dto.response.Timeframe;
import java.util.List;

public record TrendKeywordListResponse(
    Timeframe timeframe,
    List<TrendKeyword> keywords
) {

    public record TrendKeyword(
        String text, // 키워드 텍스트
        Long count, // 등장 횟수
        Float weight // 가중치 ( = count - minCount) / max(1, maxCount - minCount)
    ) {

    }
}
