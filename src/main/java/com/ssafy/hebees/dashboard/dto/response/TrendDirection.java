package com.ssafy.hebees.dashboard.dto.response;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonValue;
import io.swagger.v3.oas.annotations.media.Schema;

@Schema(description = "변화 방향", allowableValues = {"up", "down", "flat"})
public enum TrendDirection {
    UP("up"),
    DOWN("down"),
    FLAT("flat");

    private final String value;

    TrendDirection(String value) {
        this.value = value;
    }

    @JsonValue
    public String getValue() {
        return value;
    }

    @JsonCreator
    public static TrendDirection from(String v) {
        for (TrendDirection d : values()) {
            if (d.value.equalsIgnoreCase(v)) {
                return d;
            }
        }
        throw new IllegalArgumentException("Invalid direction: " + v);
    }

    public static TrendDirection of(double v) {
        if (v > 0) {
            return UP;
        } else if (v < 0) {
            return DOWN;
        } else {
            return FLAT;
        }
    }
}