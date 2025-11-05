package com.ssafy.hebees.common.util;

import java.time.Instant;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;

/**
 * 모니터링 공통 유틸리티 클래스
 */
public class MonitoringUtils {

    // Constants
    public static final ZoneId KST = ZoneId.of("Asia/Seoul");
    public static final DateTimeFormatter ISO_FORMATTER = DateTimeFormatter.ofPattern(
        "yyyy-MM-dd'T'HH:mm:ssXXX");
    public static final String NETWORK_TRAFFIC_KEY = "monitoring:network:traffic";
    public static final String NETWORK_BYTES_KEY = "monitoring:network:bytes";

    // Redis Stream 키
    public static final String CPU_STREAM_KEY = "monitoring:cpu:stream";
    public static final String MEMORY_STREAM_KEY = "monitoring:memory:stream";
    public static final String NETWORK_STREAM_KEY = "monitoring:network:stream";
    public static final double SQRT_TWO = Math.sqrt(2.0);
    public static final double BYTES_TO_GB_FACTOR = 1024.0 * 1024.0 * 1024.0;
    public static final double BYTES_TO_MBPS_FACTOR = 8.0 / (1024.0 * 1024.0);
    public static final long SECONDS_PER_DAY = 86_400;
    public static final long SECONDS_PER_HOUR = 3_600;
    public static final long SECONDS_PER_MINUTE = 60;

    /**
     * KST 시간대의 현재 시각을 ISO8601 형식으로 반환
     */
    public static String getKstTimestamp() {
        return ZonedDateTime.now(KST).format(ISO_FORMATTER);
    }

    /**
     * 값을 지정된 소수점 자리수로 반올림
     */
    public static double round(double value, int decimals) {
        if (!Double.isFinite(value)) {
            return 0.0;
        }
        double factor = Math.pow(10, decimals);
        return Math.round(value * factor) / factor;
    }

    /**
     * 바이트를 GB로 변환
     */
    public static double bytesToGb(long bytes) {
        return round(bytes / BYTES_TO_GB_FACTOR, 2);
    }

    /**
     * 바이트와 시간(초)을 Mbps로 변환
     */
    public static double bytesToMbps(long bytes, double seconds) {
        if (seconds == 0) {
            return 0.0;
        }
        return round((bytes * BYTES_TO_MBPS_FACTOR) / seconds, 1);
    }

    /**
     * Instant를 ISO8601 형식 문자열로 변환
     */
    public static String formatInstant(Instant instant) {
        if (instant == null) {
            return null;
        }
        return instant.atZone(KST).format(ISO_FORMATTER);
    }
}

