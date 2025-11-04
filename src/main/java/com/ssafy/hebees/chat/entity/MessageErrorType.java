package com.ssafy.hebees.chat.entity;

public enum MessageErrorType {
    SYSTEM,
    RESPONSE;

    public static MessageErrorType from(String value) {
        for (MessageErrorType type : values()) {
            if (type.name().equalsIgnoreCase(value)) {
                return type;
            }
        }
        throw new IllegalArgumentException("Unknown MessageErrorType: " + value);
    }
}


