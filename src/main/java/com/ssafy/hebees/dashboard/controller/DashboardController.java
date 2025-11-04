package com.ssafy.hebees.dashboard.controller;

import com.ssafy.hebees.common.response.BaseResponse;
import com.ssafy.hebees.dashboard.dto.request.TimeSeriesRequest;
import com.ssafy.hebees.dashboard.dto.response.Change24hResponse;
import com.ssafy.hebees.dashboard.dto.response.ChatbotTimeSeriesResponse;
import com.ssafy.hebees.dashboard.dto.response.HeatmapResponse;
import com.ssafy.hebees.dashboard.dto.response.ModelTimeSeriesResponse;
import com.ssafy.hebees.dashboard.dto.response.TotalDocumentsResponse;
import com.ssafy.hebees.dashboard.dto.response.TotalErrorsResponse;
import com.ssafy.hebees.dashboard.dto.response.TrendKeywordsResponse;
import com.ssafy.hebees.dashboard.service.DashboardService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
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
        return ResponseEntity.ok(
            BaseResponse.of(HttpStatus.OK, response, "일일 접속자 수 변화량 조회에 성공하였습니다."));
    }

    @GetMapping("/metrics/upload-documents/change-24h")
    @Operation(summary = "업로드 문서 수 24시간 변화 조회",
        description = "현재 시각을 기준으로 최근 24시간 동안 업로드된 문서 수와 이전 24시간 대비 증감 정보를 제공합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "조회 성공")
    })
    public ResponseEntity<BaseResponse<Change24hResponse>> getMetricsUploadDocuments() {
        Change24hResponse response = dashboardService.getUploadDocumentsChange24h();
        return ResponseEntity.ok(
            BaseResponse.of(HttpStatus.OK, response, "일일 업로드 문서 수 변화량 조회에 성공하였습니다."));
    }

    @GetMapping("/metrics/upload-documents/total")
    @Operation(summary = "총 업로드 문서 수 조회",
        description = "지금까지 업로드된 문서의 총합과 기준 시각을 조회합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "조회 성공")
    })
    public ResponseEntity<BaseResponse<TotalDocumentsResponse>> getMetricsTotalUploadDocuments() {
        TotalDocumentsResponse response = dashboardService.getTotalUploadDocuments();
        return ResponseEntity.ok(
            BaseResponse.of(HttpStatus.OK, response, "총 업로드 문서 수 조회에 성공하였습니다."));
    }

    @GetMapping("/metrics/errors/change-24h")
    @Operation(summary = "에러 수 24시간 변화 조회",
        description = "현재 시각을 기준으로 최근 24시간 동안 발생한 총 에러 수와 이전 24시간 대비 증감 정보를 제공합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "조회 성공")
    })
    public ResponseEntity<BaseResponse<Change24hResponse>> getMetricsErrors() {
        Change24hResponse response = dashboardService.getErrorsChange24h();
        return ResponseEntity.ok(
            BaseResponse.of(HttpStatus.OK, response, "일일 에러 수 변화량 조회에 성공하였습니다."));
    }

    @GetMapping("/metrics/errors/total")
    @Operation(summary = "총 에러 수 조회",
        description = "지금까지 발생한 총 에러 수와 기준 시각을 조회합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "조회 성공")
    })
    public ResponseEntity<BaseResponse<TotalErrorsResponse>> getMetricsTotalErrors() {
        TotalErrorsResponse response = dashboardService.getTotalErrors();
        return ResponseEntity.ok(BaseResponse.of(HttpStatus.OK, response, "총 에러 수 조회에 성공하였습니다."));
    }

    @GetMapping("/metrics/chatbot/timeseries")
    @Operation(summary = "챗봇 시계열 사용량 조회",
        description = "요청한 집계 단위와 기간에 따라 챗봇 사용량 시계열 데이터를 제공합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "조회 성공")
    })
    public ResponseEntity<BaseResponse<ChatbotTimeSeriesResponse>> getMetricsChatbotTimeSeries(
        @Valid @ModelAttribute TimeSeriesRequest request) {
        ChatbotTimeSeriesResponse response = dashboardService.getChatbotTimeSeries(request);
        return ResponseEntity.ok(
            BaseResponse.of(HttpStatus.OK, response, "챗봇 사용량 시계열 데이터 조회에 성공하였습니다."));
    }

    @GetMapping("/metrics/chatbot/heatmap")
    @Operation(summary = "챗봇 사용량 히트맵 조회",
        description = "이번 주(월요일~일요일) 챗봇 사용량을 1시간 단위 히트맵으로 제공합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "조회 성공")
    })
    public ResponseEntity<BaseResponse<HeatmapResponse>> getMetricsChatbotHeatmap() {
        HeatmapResponse response = dashboardService.getChatbotHeatmap();
        return ResponseEntity.ok(BaseResponse.of(HttpStatus.OK, response,
            "챗봇 사용량 히트맵 데이터 조회에 성공하였습니다."));
    }

    @GetMapping("/metrics/models/timeseries")
    @Operation(summary = "모델 별 시계열 사용량 조회",
        description = "모델 별 토큰 사용량과 평균 응답시간을 시계열로 제공합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "조회 성공")
    })
    public ResponseEntity<BaseResponse<ModelTimeSeriesResponse>> getMetricsModelsTimeSeries(
        @Valid @ModelAttribute TimeSeriesRequest request) {
        ModelTimeSeriesResponse response = dashboardService.getModelTimeSeries(request);
        return ResponseEntity.ok(BaseResponse.of(
            HttpStatus.OK, response, "모델별 사용량 시계열 데이터 조회에 성공하였습니다."));
    }

    @GetMapping("/trends/keywords")
    @Operation(summary = "대화 키워드 트렌드 조회",
        description = "최근 일별 키워드 등장 빈도를 집계하여 트렌드를 제공합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "조회 성공")
    })
    public ResponseEntity<BaseResponse<TrendKeywordsResponse>> getTrendKeywords(
        @Min(1) @Max(30) @RequestParam(defaultValue = "7") Integer scale) {
        TrendKeywordsResponse response = dashboardService.getTrendKeywords(scale);
        return ResponseEntity.ok(BaseResponse.of(HttpStatus.OK, response,
            "키워드 트렌드 데이터 조회에 성공하였습니다."));
    }
}
