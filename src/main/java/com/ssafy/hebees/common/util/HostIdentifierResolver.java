package com.ssafy.hebees.common.util;

import com.ssafy.hebees.monitoring.config.MonitoringProperties;
import java.lang.management.ManagementFactory;
import java.net.InetAddress;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

/**
 * 호스트 식별자를 해석하는 유틸리티 컴포넌트
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class HostIdentifierResolver {

    private final MonitoringProperties monitoringProperties;

    /**
     * 호스트 식별자를 해석
     * 런타임 이름
     *
     * @return 호스트 식별자 (없으면 null)
     */
    public String resolveHostIdentifier() {
        // 1. 설정된 hostIdentifier 확인
        String configured = monitoringProperties.getHostIdentifier();
        if (configured != null) {
            String trimmed = configured.trim();
            if (!trimmed.isEmpty()) {
                return trimmed;
            }
        }

        // 시스템 호스트명 확인
        try {
            String hostname = InetAddress.getLocalHost().getHostName();
            if (hostname != null && !hostname.isBlank()) {
                return hostname;
            }
        } catch (Exception e) {
            log.debug("Hostname lookup failed for host identifier", e);
        }

        // JVM 런타임 이름 확인
        try {
            String runtimeName = ManagementFactory.getRuntimeMXBean().getName();
            if (runtimeName != null && !runtimeName.isBlank()) {
                return runtimeName;
            }
        } catch (Exception e) {
            log.debug("Runtime MXBean lookup failed for host identifier", e);
        }

        return null;
    }
}

