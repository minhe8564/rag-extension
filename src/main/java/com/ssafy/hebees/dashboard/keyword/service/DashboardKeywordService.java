package com.ssafy.hebees.dashboard.keyword.service;

import com.ssafy.hebees.dashboard.keyword.dto.request.TrendKeywordCreateRequest;
import com.ssafy.hebees.dashboard.keyword.dto.request.TrendKeywordListRequest;
import com.ssafy.hebees.dashboard.keyword.dto.response.TrendKeywordCreateResponse;
import com.ssafy.hebees.dashboard.keyword.dto.response.TrendKeywordListResponse;

public interface DashboardKeywordService {

    TrendKeywordListResponse getTrendKeywords(TrendKeywordListRequest request);

    TrendKeywordCreateResponse recordTrendKeywords(TrendKeywordCreateRequest request);

}


