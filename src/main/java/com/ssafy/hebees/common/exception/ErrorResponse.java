package com.ssafy.hebees.common.exception;

import com.fasterxml.jackson.annotation.JsonInclude;
import java.util.Map;

@JsonInclude(JsonInclude.Include.NON_NULL)
public record ErrorResponse(int status, String code, String message, Map<String, String> details) {

    public static ErrorResponse of(ErrorCode errorCode) {
        return new ErrorResponse(
            errorCode.getStatus().value(),
            errorCode.name(),
            errorCode.getMessage(),
            null
        );
    }

    public static ErrorResponse of(ErrorCode errorCode, Map<String, String> details) {
        return new ErrorResponse(
            errorCode.getStatus().value(),
            errorCode.name(),
            errorCode.getMessage(),
            details
        );
    }
}
