package com.ssafy.hebees.monitoring.controller;

import com.ssafy.hebees.common.response.BaseResponse;
import com.ssafy.hebees.monitoring.dto.response.CpuUsageResponse;
import com.ssafy.hebees.monitoring.dto.response.MemoryUsageResponse;
import com.ssafy.hebees.monitoring.dto.response.NetworkTrafficResponse;
import com.ssafy.hebees.monitoring.dto.response.RunpodCpuUsageResponse;
import com.ssafy.hebees.monitoring.dto.response.RunpodGpuUsageResponse;
import com.ssafy.hebees.monitoring.dto.response.ServicePerformanceListResponse;
import com.ssafy.hebees.monitoring.dto.response.ServiceStatusListResponse;
import com.ssafy.hebees.monitoring.dto.response.StorageListResponse;
import com.ssafy.hebees.monitoring.service.MonitoringService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.http.codec.ServerSentEvent;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Flux;

@RestController
@RequestMapping("/monitoring")
@RequiredArgsConstructor
@Slf4j
@Tag(name = "시스템 모니터링", description = "시스템 리소스 모니터링 API")
public class MonitoringController {

    private final MonitoringService monitoringService;

    @GetMapping(value = "/cpu/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    @PreAuthorize("hasRole('ADMIN')")
    @Operation(summary = "CPU 사용률 스트리밍", description = "CPU 사용률을 SSE로 실시간 스트리밍합니다")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "스트리밍 시작"),
        @ApiResponse(responseCode = "403", description = "권한 없음 (ADMIN 접근 가능)")
    })
    public ResponseEntity<Flux<ServerSentEvent<CpuUsageResponse>>> streamCpuUsage() {

        HttpHeaders headers = new HttpHeaders();
        headers.add(HttpHeaders.CACHE_CONTROL, "no-cache");
        headers.add(HttpHeaders.CONNECTION, "keep-alive");
        headers.add("X-Accel-Buffering", "no");

        return ResponseEntity.ok()
            .headers(headers)
            .body(monitoringService.streamCpuUsage());
    }

    @GetMapping(value = "/memory/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    @PreAuthorize("hasRole('ADMIN')")
    @Operation(summary = "메모리 사용률 스트리밍", description = "메모리 사용률을 SSE로 실시간 스트리밍합니다")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "스트리밍 시작"),
        @ApiResponse(responseCode = "403", description = "권한 없음 (ADMIN 접근 가능)")
    })
    public ResponseEntity<Flux<ServerSentEvent<MemoryUsageResponse>>> streamMemoryUsage() {

        HttpHeaders headers = new HttpHeaders();
        headers.add(HttpHeaders.CACHE_CONTROL, "no-cache");
        headers.add(HttpHeaders.CONNECTION, "keep-alive");
        headers.add("X-Accel-Buffering", "no");

        return ResponseEntity.ok()
            .headers(headers)
            .body(monitoringService.streamMemoryUsage());
    }

    @GetMapping(value = "/network/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    @PreAuthorize("hasRole('ADMIN')")
    @Operation(summary = "네트워크 트래픽 스트리밍", description = "네트워크 트래픽을 SSE로 실시간 스트리밍합니다")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "스트리밍 시작"),
        @ApiResponse(responseCode = "403", description = "권한 없음 (ADMIN 접근 가능)")
    })
    public ResponseEntity<Flux<ServerSentEvent<NetworkTrafficResponse>>> streamNetworkTraffic() {

        HttpHeaders headers = new HttpHeaders();
        headers.add(HttpHeaders.CACHE_CONTROL, "no-cache");
        headers.add(HttpHeaders.CONNECTION, "keep-alive");
        headers.add("X-Accel-Buffering", "no");

        return ResponseEntity.ok()
            .headers(headers)
            .body(monitoringService.streamNetworkTraffic());
    }

    @GetMapping(value = "/services", produces = MediaType.APPLICATION_JSON_VALUE)
    @PreAuthorize("hasRole('ADMIN')")
    @Operation(summary = "서비스별 성능 조회",
        description = "설정된 모니터링 대상 서비스의 CPU/메모리/Load 지표와 상태를 조회합니다. " +
            "monitoring.service-targets 설정에 따라 조회하는 서비스들을 동적으로 변경됩니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "조회 성공"),
        @ApiResponse(responseCode = "401", description = "인증 실패"),
        @ApiResponse(responseCode = "403", description = "권한 없음 (ADMIN 접근 가능)")
    })
    public ResponseEntity<BaseResponse<ServicePerformanceListResponse>> getServicePerformance() {
        ServicePerformanceListResponse response = monitoringService.getServicePerformance();
        int serviceCount = response.services().size();
        String message = serviceCount > 0
            ? String.format("%d개의 서비스 성능 정보를 조회했습니다.", serviceCount)
            : "모니터링 대상 서비스가 없습니다.";
        return ResponseEntity.ok(BaseResponse.of(
            HttpStatus.OK,
            response,
            message
        ));
    }

    @GetMapping(value = "/services/status", produces = MediaType.APPLICATION_JSON_VALUE)
    @PreAuthorize("hasRole('ADMIN')")
    @Operation(summary = "서비스 상태 조회",
        description = "지정된 핵심 서비스들의 실행 상태를 가져와서 조회합니다")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "조회 성공"),
        @ApiResponse(responseCode = "401", description = "인증 실패"),
        @ApiResponse(responseCode = "403", description = "권한 없음 (ADMIN 사용)")
    })
    public ResponseEntity<BaseResponse<ServiceStatusListResponse>> getServiceStatus() {
        ServiceStatusListResponse response = monitoringService.getServiceStatus();
        int count = response.services() == null ? 0 : response.services().size();
        String message = count > 0
            ? String.format("%d개의 서비스 상태를 조회했습니다.", count)
            : "모니터링 대상 서비스가 설정되어 있지 않습니다.";
        return ResponseEntity.ok(BaseResponse.of(
            HttpStatus.OK,
            response,
            message
        ));
    }

    @GetMapping(value = "/storage", produces = MediaType.APPLICATION_JSON_VALUE)
    @PreAuthorize("hasRole('ADMIN')")
    @Operation(summary = "스토리지 사용량 조회",
        description = "주요 파일시스템 경로의 디스크 총 용량, 사용 용량 및 사용률을 조회합니다")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "조회 성공"),
        @ApiResponse(responseCode = "401", description = "인증 실패"),
        @ApiResponse(responseCode = "403", description = "권한 없음 (ADMIN 접근 가능)")
    })
    public ResponseEntity<BaseResponse<StorageListResponse>> getStorageInfo() {
        StorageListResponse response = monitoringService.getStorageInfo();
        return ResponseEntity.ok(BaseResponse.of(
            HttpStatus.OK,
            response,
            "스토리지 사용량 정보를 조회하였습니다."
        ));
    }

    @GetMapping(value = "/runpod/{podId}/gpu", produces = MediaType.APPLICATION_JSON_VALUE)
    @PreAuthorize("hasRole('ADMIN')")
    @Operation(summary = "Runpod GPU 사용량 조회", description = "Runpod 공식 API를 통해 Pod의 GPU 사용량을 조회합니다")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "조회 성공"),
        @ApiResponse(responseCode = "403", description = "권한 없음 (ADMIN 접근 가능)")
    })
    public ResponseEntity<BaseResponse<RunpodGpuUsageResponse>> getRunpodGpuUsage(
        @PathVariable String podId
    ) {
        RunpodGpuUsageResponse response = monitoringService.getRunpodGpuUsage(podId);
        return ResponseEntity.ok(BaseResponse.of(
            HttpStatus.OK,
            response,
            "Runpod GPU 사용량 조회 성공"
        ));
    }

    @GetMapping(value = "/runpod/{podId}/cpu", produces = MediaType.APPLICATION_JSON_VALUE)
    @PreAuthorize("hasRole('ADMIN')")
    @Operation(summary = "Runpod CPU 사용량 조회", description = "Runpod 공식 API를 통해 Pod의 CPU 사용량을 조회합니다")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "조회 성공"),
        @ApiResponse(responseCode = "403", description = "권한 없음 (ADMIN 접근 가능)")
    })
    public ResponseEntity<BaseResponse<RunpodCpuUsageResponse>> getRunpodCpuUsage(
        @PathVariable String podId
    ) {
        RunpodCpuUsageResponse response = monitoringService.getRunpodCpuUsage(podId);
        return ResponseEntity.ok(BaseResponse.of(
            HttpStatus.OK,
            response,
            "Runpod CPU 사용량 조회 성공"
        ));
    }
}
