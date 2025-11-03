package com.ssafy.hebees.common.response;

import com.fasterxml.jackson.annotation.JsonInclude;
import org.springframework.http.HttpStatus;

@JsonInclude(JsonInclude.Include.NON_NULL)
public record BaseResponse<T>(
    int status,
    String code,
    String message,
    boolean isSuccess,
    T result
) {

    public static <T> BaseResponse<T> success(T result) {
        return of(HttpStatus.OK, result);
    }

    public static <T> BaseResponse<T> of(HttpStatus status, T result) {
        return of(status, result, "요청에 성공하였습니다.");
    }

    public static <T> BaseResponse<T> of(HttpStatus status, T result, String message) {
        boolean success = status.is2xxSuccessful();
        String code = status.name();
        return new BaseResponse<>(status.value(), code, message, success, result);
    }

    public static <T> BaseResponse<T> error(HttpStatus status, String code, String message,
        T result) {
        return new BaseResponse<>(status.value(), code, message, false, result);
    }
}
