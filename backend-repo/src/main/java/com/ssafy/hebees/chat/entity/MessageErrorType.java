package com.ssafy.hebees.chat.entity;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonValue;

public enum MessageErrorType {
    SYSTEM,
    RESPONSE;

    @JsonCreator
    public static MessageErrorType from(String value) {
        if (value == null) {
            throw new IllegalArgumentException("MessageErrorType cannot be null");
        }
        for (MessageErrorType type : values()) {
            if (type.name().equalsIgnoreCase(value)) {
                return type;
            }
        }
        throw new IllegalArgumentException("Unknown MessageErrorType: " + value);
    }

    @JsonValue
    public String toValue() {
        return name().toLowerCase();
    }
}

