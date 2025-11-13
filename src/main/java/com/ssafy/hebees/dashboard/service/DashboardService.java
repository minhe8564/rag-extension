package com.ssafy.hebees.dashboard.service;

import com.ssafy.hebees.dashboard.dto.response.Change24hResponse;
import com.ssafy.hebees.dashboard.dto.response.TotalDocumentsResponse;
import com.ssafy.hebees.dashboard.dto.response.TotalErrorsResponse;
import com.ssafy.hebees.dashboard.dto.response.TotalUsersResponse;

public interface DashboardService {

    // 변화량

    Change24hResponse getAccessUsersChange24h();

    Change24hResponse getUploadDocumentsChange24h();

    Change24hResponse getErrorsChange24h();

    // 총합

    TotalUsersResponse getTotalUsers();

    TotalDocumentsResponse getTotalUploadDocuments();

    TotalErrorsResponse getTotalErrors();

}

