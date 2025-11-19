package com.ssafy.hebees.dashboard.keyword.controller;

import com.ssafy.hebees.common.response.BaseResponse;
import com.ssafy.hebees.dashboard.keyword.dto.request.TrendKeywordListRequest;
import com.ssafy.hebees.dashboard.keyword.dto.request.TrendKeywordRegisterRequest;
import com.ssafy.hebees.dashboard.keyword.dto.response.TrendKeywordListResponse;
import com.ssafy.hebees.dashboard.keyword.dto.response.TrendKeywordRegisterResponse;
import com.ssafy.hebees.dashboard.keyword.service.DashboardKeywordService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/analytics/trends/keywords")
@RequiredArgsConstructor
@Slf4j
@Tag(name = "대시보드 - 키워드", description = "대시보드 키워드 API")
public class DashboardKeywordController {

    private final DashboardKeywordService dashboardKeywordService;

    @GetMapping
    @Operation(summary = "대화 키워드 트렌드 조회", description = "최근 일별 키워드 등장 빈도를 집계하여 트렌드를 제공합니다.")
    @ApiResponse(responseCode = "200", description = "트렌드 키워드 조회 성공")
    public ResponseEntity<BaseResponse<TrendKeywordListResponse>> getTrendKeywords(
        @Valid @ModelAttribute TrendKeywordListRequest request
    ) {
        TrendKeywordListResponse response = dashboardKeywordService.getKeywords(request);
        return ResponseEntity.ok(BaseResponse.of(HttpStatus.OK, response,
            String.format("최근 %d일 자주 물어보는 키워드를 조회하였습니다.", request.scale())
        ));
    }

    @PostMapping
    @Operation(summary = "대화 키워드 트렌드 등록", description = "사용자 질의를 트렌드 키워드 집계에 반영합니다.")
    @ApiResponse(responseCode = "201", description = "트렌드 키워드 등록 성공")
    public ResponseEntity<BaseResponse<TrendKeywordRegisterResponse>> recordTrendKeywords(
        @Valid @RequestBody TrendKeywordRegisterRequest request
    ) {
        TrendKeywordRegisterResponse response = dashboardKeywordService.registerKeywords(request);
        return ResponseEntity.ok(BaseResponse.of(HttpStatus.CREATED, response, "키워드를 등록하였습니다."));
    }
}
