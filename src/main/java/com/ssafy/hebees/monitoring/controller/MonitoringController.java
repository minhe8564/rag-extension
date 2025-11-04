package com.ssafy.hebees.monitoring.controller;

import com.ssafy.hebees.monitoring.dto.response.CpuUsageResponse;
import com.ssafy.hebees.monitoring.dto.response.MemoryUsageResponse;
import com.ssafy.hebees.monitoring.dto.response.NetworkTrafficResponse;
import com.ssafy.hebees.monitoring.service.MonitoringService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.http.codec.ServerSentEvent;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
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
    @Operation(summary = "CPU 사용률 스트리밍", description = "CPU 사용률을 SSE로 실시간 스트리밍합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "스트리밍 시작"),
        @ApiResponse(responseCode = "403", description = "권한 없음 (ADMIN만 접근 가능)")
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
    @Operation(summary = "메모리 사용량 스트리밍", description = "메모리 사용량을 SSE로 실시간 스트리밍합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "스트리밍 시작"),
        @ApiResponse(responseCode = "403", description = "권한 없음 (ADMIN만 접근 가능)")
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
    @Operation(summary = "네트워크 트래픽 스트리밍", description = "네트워크 트래픽을 SSE로 실시간 스트리밍합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "스트리밍 시작"),
        @ApiResponse(responseCode = "403", description = "권한 없음 (ADMIN만 접근 가능)")
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
}

