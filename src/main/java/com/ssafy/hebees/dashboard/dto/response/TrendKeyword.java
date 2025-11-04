package com.ssafy.hebees.dashboard.dto.response;

public record TrendKeyword(
    String text, // 키워드 텍스트
    Long count, // 등장 횟수
    Float weight // 가중치 ( = count - minCount) / max(1, maxCount - minCount)
) {

}
