package com.ssafy.hebees.common.exception;

import lombok.Getter;

@Getter
public class CustomJwtException extends RuntimeException {

    private final ErrorCode errorCode;

    public CustomJwtException(ErrorCode errorCode) {
        super(errorCode.getMessage());
        this.errorCode = errorCode;
    }

    public CustomJwtException(ErrorCode errorCode, String message) {
        super(message);
        this.errorCode = errorCode;
    }

    public CustomJwtException(ErrorCode errorCode, Throwable cause) {
        super(errorCode.getMessage(), cause);
        this.errorCode = errorCode;
    }
}

