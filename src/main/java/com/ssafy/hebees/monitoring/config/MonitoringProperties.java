package com.ssafy.hebees.monitoring.config;

import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

import java.util.Collections;
import java.util.List;

@Getter
@Setter
@Component
@ConfigurationProperties(prefix = "monitoring")
public class MonitoringProperties {

    /**
     * 네트워크 대역폭(Mbps). cAdvisor 메트릭에 값이 없을 때 사용하는 기본값.
     */
    private double networkBandwidthMbps = 1000.0;

    /**
     * 모니터링 대상 서비스/컨테이너 식별자 목록.
     */
    private List<String> serviceTargets = Collections.emptyList();
}
