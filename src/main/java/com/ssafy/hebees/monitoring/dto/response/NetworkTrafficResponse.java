package com.ssafy.hebees.monitoring.dto.response;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.DecimalMin;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Schema(description = "네트워크 트래픽 응답")
@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class NetworkTrafficResponse {

    @Schema(description = "이벤트 생성 시각 (ISO8601)", example = "2025-11-03T18:20:00+09:00")
    private String timestamp;

    @Schema(description = "실시간 Inbound 속도(Mbps)", example = "12.4")
    @DecimalMin(value = "0.0")
    private double inboundMbps;

    @Schema(description = "실시간 Outbound 속도(Mbps)", example = "8.7")
    @DecimalMin(value = "0.0")
    private double outboundMbps;

    @Schema(description = "네트워크 총 대역폭(Mbps)", example = "1000.0")
    @DecimalMin(value = "0.0")
    private double bandwidthMbps;
}

