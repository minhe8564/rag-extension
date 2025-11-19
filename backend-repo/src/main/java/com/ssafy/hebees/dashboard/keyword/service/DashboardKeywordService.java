package com.ssafy.hebees.dashboard.keyword.service;

import com.ssafy.hebees.dashboard.keyword.dto.request.TrendKeywordRegisterRequest;
import com.ssafy.hebees.dashboard.keyword.dto.request.TrendKeywordListRequest;
import com.ssafy.hebees.dashboard.keyword.dto.response.TrendKeywordRegisterResponse;
import com.ssafy.hebees.dashboard.keyword.dto.response.TrendKeywordListResponse;

public interface DashboardKeywordService {

    TrendKeywordListResponse getKeywords(TrendKeywordListRequest request);

    TrendKeywordRegisterResponse registerKeywords(TrendKeywordRegisterRequest request);

}
