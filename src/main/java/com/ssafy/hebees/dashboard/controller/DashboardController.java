package com.ssafy.hebees.dashboard.controller;

import com.ssafy.hebees.common.response.BaseResponse;
import com.ssafy.hebees.dashboard.dto.request.ErrorMetricIncrementRequest;
import com.ssafy.hebees.dashboard.dto.request.MetricIncrementRequest;
import com.ssafy.hebees.dashboard.dto.request.ModelExpenseUsageRequest;
import com.ssafy.hebees.dashboard.dto.request.TimeSeriesRequest;
import com.ssafy.hebees.dashboard.keyword.dto.request.TrendKeywordCreateRequest;
import com.ssafy.hebees.dashboard.keyword.dto.request.TrendKeywordListRequest;
import com.ssafy.hebees.dashboard.dto.response.Change24hResponse;
import com.ssafy.hebees.dashboard.model.dto.response.ChatbotTimeSeriesResponse;
import com.ssafy.hebees.dashboard.chat.dto.response.ChatroomsTodayResponse;
import com.ssafy.hebees.dashboard.chat.dto.response.ErrorsTodayResponse;
import com.ssafy.hebees.dashboard.model.dto.response.HeatmapResponse;
import com.ssafy.hebees.dashboard.dto.response.ModelPriceResponse;
import com.ssafy.hebees.dashboard.model.dto.response.ModelTimeSeriesResponse;
import com.ssafy.hebees.dashboard.dto.response.TotalDocumentsResponse;
import com.ssafy.hebees.dashboard.dto.response.TotalErrorsResponse;
import com.ssafy.hebees.dashboard.dto.response.TotalUsersResponse;
import com.ssafy.hebees.dashboard.keyword.dto.response.TrendKeywordCreateResponse;
import com.ssafy.hebees.dashboard.keyword.dto.response.TrendKeywordListResponse;
import com.ssafy.hebees.dashboard.chat.service.DashboardChatService;
import com.ssafy.hebees.dashboard.keyword.service.DashboardKeywordService;
import com.ssafy.hebees.dashboard.model.service.DashboardModelService;
import com.ssafy.hebees.dashboard.service.DashboardMetricStreamService;
import com.ssafy.hebees.dashboard.service.DashboardService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

@RestController
@RequestMapping("/analytics")
@RequiredArgsConstructor
@Slf4j
@Tag(name = "대시보드", description = "대시보드 API")
@Validated
public class DashboardController {

    private final DashboardService dashboardService;
    private final DashboardMetricStreamService dashboardMetricStreamService;
    private final DashboardChatService dashboardChatService;
    private final DashboardKeywordService dashboardKeywordService;
    private final DashboardModelService dashboardModelService;

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

    @GetMapping("/metrics/access-users/total")
    @Operation(summary = "총 접속자 수 조회",
        description = "지금까지 집계된 접속자 수의 총합과 기준 시각을 조회합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "조회 성공")
    })
    public ResponseEntity<BaseResponse<TotalUsersResponse>> getMetricsTotalUsers() {
        TotalUsersResponse response = dashboardService.getTotalUsers();
        return ResponseEntity.ok(
            BaseResponse.of(HttpStatus.OK, response, "총 접속자 수 조회에 성공하였습니다."));
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

    @GetMapping(value = "/metrics/access-users/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    @Operation(summary = "접속자 수 SSE 알림",
        description = "접속자 수의 변화가 있을 때 SSE로 알림을 보냅니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "SSE 연결 성공")
    })
    public SseEmitter subscribeAccessUsersSSE(
        @RequestHeader(name = "Last-Event-ID", required = false) String lastEventId
    ) {
        return dashboardMetricStreamService.subscribeAccessUsers(lastEventId);
    }

    @GetMapping(value = "/metrics/upload-documents/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    @Operation(summary = "업로드된 문서 수 SSE 알림",
        description = "업로드된 문서 수의 변화가 있을 때 SSE로 알림을 보냅니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "SSE 연결 성공")
    })
    public SseEmitter subscribeUploadDocumentsSSE(
        @RequestHeader(name = "Last-Event-ID", required = false) String lastEventId
    ) {
        return dashboardMetricStreamService.subscribeUploadDocuments(lastEventId);
    }

    @GetMapping(value = "/metrics/errors/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    @Operation(summary = "에러 수 SSE 알림",
        description = "에러 수의 변화가 있을 때 SSE로 알림을 보냅니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "SSE 연결 성공")
    })
    public SseEmitter subscribeErrorsSSE(
        @RequestHeader(name = "Last-Event-ID", required = false) String lastEventId
    ) {
        return dashboardMetricStreamService.subscribeErrors(lastEventId);
    }

    @GetMapping(value = "/metrics/expense/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    @Operation(summary = "모델 비용 SSE 스트림",
        description = "모델별 토큰 비용 누적 현황을 SSE로 스트리밍합니다. 초기 스냅샷과 이후 변경사항이 전송됩니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "SSE 연결 성공")
    })
    public SseEmitter subscribeExpenseStream(
        @RequestHeader(name = "Last-Event-ID", required = false) String lastEventId
    ) {
        return dashboardModelService.subscribeExpenseStream(lastEventId);
    }

    @PostMapping("/metrics/models/increment")
    @Operation(summary = "모델 사용량 갱신", description = "모델별 입력/출력 토큰 사용량과 응답 시간을 기록하고 SSE 구독자에게 최신 비용 정보를 전송합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "집계 및 SSE 갱신 성공")
    })
    public ResponseEntity<BaseResponse<ModelPriceResponse>> recordExpenseUsage(
        @Valid @RequestBody ModelExpenseUsageRequest request
    ) {
        ModelPriceResponse response = dashboardModelService.recordExpenseUsage(request);
        return ResponseEntity.ok(
            BaseResponse.of(HttpStatus.OK, response, "모델 비용 집계를 업데이트하였습니다."));
    }

    @PostMapping("/metrics/access-users/increment")
    @Operation(summary = "접속자 수 증가 기록", description = "현재 시간대의 접속자 수를 n만큼 증가시킵니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "증분 기록 성공")
    })
    public ResponseEntity<BaseResponse<Long>> incrementAccessUsers(
        @Valid @RequestBody MetricIncrementRequest request
    ) {
        long updated = dashboardMetricStreamService.incrementCurrentAccessUsers(request.amount());
        return ResponseEntity.ok(
            BaseResponse.of(HttpStatus.OK, updated, "현재 시간대 접속자 수가 업데이트되었습니다."));
    }

    @PostMapping("/metrics/upload-documents/increment")
    @Operation(summary = "업로드 문서 수 증가 기록", description = "현재 시간대의 업로드 문서 수를 n만큼 증가시킵니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "증분 기록 성공")
    })
    public ResponseEntity<BaseResponse<Long>> incrementUploadDocuments(
        @Valid @RequestBody MetricIncrementRequest request
    ) {
        long updated = dashboardMetricStreamService.incrementCurrentUploadDocuments(
            request.amount());
        return ResponseEntity.ok(
            BaseResponse.of(HttpStatus.OK, updated, "현재 시간대 업로드 문서 수가 업데이트되었습니다."));
    }

    @PostMapping("/metrics/errors/increment")
    @Operation(summary = "에러 수 증가 기록", description = "현재 시간대의 에러 집계 값을 증가시킵니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "증분 기록 성공")
    })
    public ResponseEntity<BaseResponse<Long>> incrementErrors(
        @Valid @RequestBody ErrorMetricIncrementRequest request
    ) {
        long updated = dashboardMetricStreamService.incrementCurrentErrors(
            request.systemCount(), request.responseCount());
        return ResponseEntity.ok(
            BaseResponse.of(HttpStatus.OK, updated, "현재 시간대 에러 수가 업데이트되었습니다."));
    }

    @GetMapping(value = "/metrics/chatbot/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    @Operation(summary = "실시간 챗봇 요청 수",
        description = "실시간 챗봇 요청 수를 10초 마다 SSE로 스트리밍합니다.")
    @ApiResponse(responseCode = "200", description = "SSE 연결 성공")
    public SseEmitter subscribeChatbotStream(
        @RequestHeader(name = "Last-Event-ID", required = false) String lastEventId
    ) {
        return dashboardModelService.subscribeChatbotStream(lastEventId);
    }

    @PostMapping("/metrics/chatbot/increment")
    @Operation(summary = "챗봇 요청 수 증가 기록",
        description = "10초 버킷에 챗봇 요청 횟수를 지정한 만큼 증가시킵니다.")
    @ApiResponse(responseCode = "200", description = "증분 기록 성공")
    public ResponseEntity<BaseResponse<Void>> incrementChatbotRequests(
        @Valid @RequestBody MetricIncrementRequest request
    ) {
        dashboardModelService.incrementChatbotRequests(request.amount());

        return ResponseEntity.ok(
            BaseResponse.of(HttpStatus.OK, null, "챗봇 요청 수가 업데이트되었습니다."));
    }

    @GetMapping("/metrics/chatbot/timeseries")
    @Operation(summary = "챗봇 시계열 사용량 조회",
        description = "요청한 집계 단위와 기간에 따라 챗봇 사용량 시계열 데이터를 제공합니다.")
    @ApiResponse(responseCode = "200", description = "조회 성공")
    public ResponseEntity<BaseResponse<ChatbotTimeSeriesResponse>> getMetricsChatbotTimeSeries(
        @Valid @ModelAttribute TimeSeriesRequest request) {
        ChatbotTimeSeriesResponse response = dashboardModelService.getChatbotTimeSeries(request);
        return ResponseEntity.ok(
            BaseResponse.of(HttpStatus.OK, response, "챗봇 사용량 시계열 데이터 조회에 성공하였습니다."));
    }

    @GetMapping("/metrics/chatbot/heatmap")
    @Operation(summary = "챗봇 사용량 히트맵 조회",
        description = "이번 주(월요일~일요일) 챗봇 사용량을 1시간 단위 히트맵으로 제공합니다.")
    @ApiResponse(responseCode = "200", description = "조회 성공")
    public ResponseEntity<BaseResponse<HeatmapResponse>> getMetricsChatbotHeatmap() {
        HeatmapResponse response = dashboardModelService.getChatbotHeatmap();
        return ResponseEntity.ok(BaseResponse.of(HttpStatus.OK, response,
            "챗봇 사용량 히트맵 데이터 조회에 성공하였습니다."));
    }

    @GetMapping("/metrics/models/timeseries")
    @Operation(summary = "모델 별 시계열 사용량 조회",
        description = "모델 별 토큰 사용량과 평균 응답시간을 시계열로 제공합니다.")
    @ApiResponse(responseCode = "200", description = "조회 성공")
    public ResponseEntity<BaseResponse<ModelTimeSeriesResponse>> getMetricsModelsTimeSeries(
        @Valid @ModelAttribute TimeSeriesRequest request) {
        ModelTimeSeriesResponse response = dashboardModelService.getModelTimeSeries(request);
        return ResponseEntity.ok(BaseResponse.of(
            HttpStatus.OK, response, "모델별 사용량 시계열 데이터 조회에 성공하였습니다."));
    }

    @GetMapping("/trends/keywords")
    @Operation(summary = "대화 키워드 트렌드 조회",
        description = "최근 일별 키워드 등장 빈도를 집계하여 트렌드를 제공합니다.")
    @ApiResponse(responseCode = "200", description = "조회 성공")
    public ResponseEntity<BaseResponse<TrendKeywordListResponse>> getTrendKeywords(
        @Valid TrendKeywordListRequest request) {
        TrendKeywordListResponse response = dashboardKeywordService.getTrendKeywords(request);
        return ResponseEntity.ok(BaseResponse.of(HttpStatus.OK, response,
            String.format("최근 %d일 자주 물어보는 키워드를 조회하였습니다.", request.scale())
        ));
    }

    @PostMapping(value = "/trends/keywords")
    @Operation(summary = "대화 키워드 트렌드 등록", description = "사용자 질의를 트렌드 키워드 집계에 반영합니다.")
    @ApiResponse(responseCode = "200", description = "키워드 집계 성공")
    public ResponseEntity<BaseResponse<TrendKeywordCreateResponse>> recordTrendKeywords(
        @Valid @RequestBody TrendKeywordCreateRequest request
    ) {
        TrendKeywordCreateResponse response = dashboardKeywordService.recordTrendKeywords(request);
        return ResponseEntity.ok(
            BaseResponse.of(HttpStatus.OK, response, "키워드를 등록하였습니다."));
    }

    @GetMapping("/chatrooms/today")
    @Operation(summary = "오늘 생성된 챗룸 조회",
        description = "오늘 생성된 최신 챗룸 목록과 사용자 정보를 제공합니다.")
    @ApiResponse(responseCode = "200", description = "조회 성공")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<BaseResponse<ChatroomsTodayResponse>> getChatroomsToday() {
        ChatroomsTodayResponse response = dashboardChatService.getChatroomsToday();
        return ResponseEntity.ok(BaseResponse.of(HttpStatus.OK, response,
            "오늘 생성된 챗룸 목록 조회에 성공하였습니다."));
    }

    @GetMapping("/errors/today")
    @Operation(summary = "오늘 발생한 메시지 에러 조회",
        description = "오늘 발생한 최근 메시지 에러 목록과 관련된 세션 정보를 제공합니다.")
    @ApiResponse(responseCode = "200", description = "조회 성공")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<BaseResponse<ErrorsTodayResponse>> getErrorsToday() {
        ErrorsTodayResponse response = dashboardChatService.getErrorsToday();
        return ResponseEntity.ok(BaseResponse.of(HttpStatus.OK, response,
            "오늘 발생한 메시지 에러 조회에 성공하였습니다."));
    }
}
