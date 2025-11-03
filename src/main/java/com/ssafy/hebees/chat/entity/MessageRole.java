package com.ssafy.hebees.chat.entity;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonValue;
import java.util.Arrays;

public enum MessageRole {
    USER("user"),
    ASSISTANT("assistant"),
    SYSTEM("system"),
    TOOL("tool");

    private final String value;

    MessageRole(String value) {
        this.value = value;
    }

    @JsonValue
    public String getValue() {
        return value;
    }

    @JsonCreator
    public static MessageRole from(String v) {
        return Arrays.stream(values())
            .filter(e -> e.value.equalsIgnoreCase(v))
            .findFirst()
            .orElseThrow(() -> new IllegalArgumentException("Unknown MessageRole: " + v));
    }

    @Override
    public String toString() {
        return value;
    }
}

