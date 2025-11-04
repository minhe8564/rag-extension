package com.ssafy.hebees.dashboard.service;

import com.ssafy.hebees.dashboard.dto.request.TimeSeriesRequest;
import com.ssafy.hebees.dashboard.dto.response.Change24hResponse;
import com.ssafy.hebees.dashboard.dto.response.ChatbotTimeSeriesResponse;
import com.ssafy.hebees.dashboard.dto.response.HeatmapResponse;
import com.ssafy.hebees.dashboard.dto.response.ModelTimeSeriesResponse;
import com.ssafy.hebees.dashboard.dto.response.TotalDocumentsResponse;
import com.ssafy.hebees.dashboard.dto.response.TotalErrorsResponse;

public interface DashboardService {

    Change24hResponse getAccessUsersChange24h();

    Change24hResponse getUploadDocumentsChange24h();

    TotalDocumentsResponse getTotalUploadDocuments();

    Change24hResponse getErrorsChange24h();

    TotalErrorsResponse getTotalErrors();

    ChatbotTimeSeriesResponse getChatbotTimeSeries(TimeSeriesRequest request);

    ModelTimeSeriesResponse getModelTimeSeries(TimeSeriesRequest request);

    HeatmapResponse getChatbotHeatmap();
}

