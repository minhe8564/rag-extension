package com.ssafy.hebees.dashboard.dto;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonValue;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Getter;

@Schema(enumAsRef = true, description = "집계 간격", allowableValues = {"day", "week", "month"})
public enum Granularity {
    DAY("day", 30),
    WEEK("week", 12),
    MONTH("month", 12);

    private final String value;
    @Getter
    private final int defaultScale;

    Granularity(String value, int defaultScale) {
        this.value = value;
        this.defaultScale = defaultScale;
    }

    /**
     * 직렬화 시 "day"/"week"/"month"로 출력
     */
    @JsonValue
    public String getValue() {
        return value;
    }

    /**
     * 역직렬화/바인딩 시 대소문자 무시하고 매핑
     */
    @JsonCreator
    public static Granularity from(String s) {
        for (Granularity g : values()) {
            if (g.value.equalsIgnoreCase(s)) {
                return g;
            }
        }
        throw new IllegalArgumentException("Invalid granularity: " + s);
    }
}
