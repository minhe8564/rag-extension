package com.ssafy.hebees.dashboard.controller;

import com.ssafy.hebees.common.response.BaseResponse;
import com.ssafy.hebees.dashboard.dto.response.Change24hResponse;
import com.ssafy.hebees.dashboard.dto.response.TotalDocumentsResponse;
import com.ssafy.hebees.dashboard.dto.response.TotalErrorsResponse;
import com.ssafy.hebees.dashboard.service.DashboardService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/analytics")
@RequiredArgsConstructor
@Slf4j
@Tag(name = "대시보드", description = "대시보드 API")
@Validated
public class DashboardController {

    private final DashboardService dashboardService;

    @GetMapping("/metrics/access-users/change-24h")
    @Operation(summary = "접속자 수 24시간 변화 조회",
        description = "현재 시각을 기준으로 최근 24시간 동안의 접속자 수와 이전 24시간 대비 증감 정보를 제공합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "조회 성공")
    })
    public ResponseEntity<BaseResponse<Change24hResponse>> getMetricsAccessUsers() {
        Change24hResponse response = dashboardService.getAccessUsersChange24h();
        return ResponseEntity.ok(BaseResponse.success(response));
    }

    @GetMapping("/metrics/upload-documents/change-24h")
    @Operation(summary = "업로드 문서 수 24시간 변화 조회",
        description = "현재 시각을 기준으로 최근 24시간 동안 업로드된 문서 수와 이전 24시간 대비 증감 정보를 제공합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "조회 성공")
    })
    public ResponseEntity<BaseResponse<Change24hResponse>> getMetricsUploadDocuments() {
        Change24hResponse response = dashboardService.getUploadDocumentsChange24h();
        return ResponseEntity.ok(BaseResponse.success(response));
    }

    @GetMapping("/metrics/upload-documents/total")
    @Operation(summary = "총 업로드 문서 수 조회",
        description = "지금까지 업로드된 문서의 총합과 기준 시각을 조회합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "조회 성공")
    })
    public ResponseEntity<BaseResponse<TotalDocumentsResponse>> getMetricsTotalUploadDocuments() {
        TotalDocumentsResponse response = dashboardService.getTotalUploadDocuments();
        return ResponseEntity.ok(BaseResponse.success(response));
    }

    @GetMapping("/metrics/errors/change-24h")
    @Operation(summary = "에러 수 24시간 변화 조회",
        description = "현재 시각을 기준으로 최근 24시간 동안 발생한 총 에러 수와 이전 24시간 대비 증감 정보를 제공합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "조회 성공")
    })
    public ResponseEntity<BaseResponse<Change24hResponse>> getMetricsErrors() {
        Change24hResponse response = dashboardService.getErrorsChange24h();
        return ResponseEntity.ok(BaseResponse.success(response));
    }

    @GetMapping("/metrics/errors/total")
    @Operation(summary = "총 에러 수 조회",
        description = "지금까지 발생한 총 에러 수와 기준 시각을 조회합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "조회 성공")
    })
    public ResponseEntity<BaseResponse<TotalErrorsResponse>> getMetricsTotalErrors() {
        TotalErrorsResponse response = dashboardService.getTotalErrors();
        return ResponseEntity.ok(BaseResponse.success(response));
    }
}
