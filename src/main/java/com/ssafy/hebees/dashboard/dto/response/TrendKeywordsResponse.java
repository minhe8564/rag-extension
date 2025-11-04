package com.ssafy.hebees.dashboard.dto.response;

import java.util.List;

public record TrendKeywordsResponse(
    Timeframe timeframe,
    List<TrendKeyword> keywords
) {

}
