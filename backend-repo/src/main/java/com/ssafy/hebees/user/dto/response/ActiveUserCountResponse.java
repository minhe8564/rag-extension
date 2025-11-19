package com.ssafy.hebees.user.dto.response;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.ssafy.hebees.common.util.MonitoringUtils;

public record ActiveUserCountResponse(
    @JsonProperty("activeUserCount")
    long activeUserCount,

    @JsonProperty("timestamp")
    String timestamp
) {

    public static ActiveUserCountResponse of(long count) {
        String kstTimestamp = MonitoringUtils.getKstTimestamp();
        return new ActiveUserCountResponse(count, kstTimestamp);
    }
}
