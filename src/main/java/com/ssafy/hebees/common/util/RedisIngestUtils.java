package com.ssafy.hebees.common.util;

import java.util.UUID;

/**
 * Ingest 영역에서 사용하는 Redis 키 유틸리티. 네임스페이스 및 키 규칙을 단일 장소에서 관리합니다.
 */
public final class RedisIngestUtils {

    private static final String NS = "ingest";
    private static final String SEP = ":";

    private RedisIngestUtils() {
    }

    public static String userRunsKey(UUID userUuid) {
        return userRunsKey(userUuid.toString());
    }

    public static String userRunsKey(String userUuid) {
        return NS + SEP + "user" + SEP + userUuid + SEP + "runs";
    }

    public static String runMetaKey(String runId) {
        return NS + SEP + "run" + SEP + runId + SEP + "meta";
    }

    public static String runEventsKey(String runId) {
        return NS + SEP + "run" + SEP + runId + SEP + "events";
    }
}

