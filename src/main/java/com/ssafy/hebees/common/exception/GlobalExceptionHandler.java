package com.ssafy.hebees.common.exception;

import com.ssafy.hebees.common.response.BaseResponse;
import io.swagger.v3.oas.annotations.Hidden;
import jakarta.validation.ConstraintViolation;
import jakarta.validation.ConstraintViolationException;
import java.util.Map;
import java.util.stream.Collectors;
import lombok.extern.slf4j.Slf4j;
import org.apache.catalina.connector.ClientAbortException;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotWritableException;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.context.request.async.AsyncRequestNotUsableException;

@Slf4j
@RestControllerAdvice
@Hidden
public class GlobalExceptionHandler {

    /* 1) 비즈니스 예외 */
    @ExceptionHandler(BusinessException.class)
    protected ResponseEntity<BaseResponse<Object>> handleBusinessException(BusinessException e) {
        ErrorCode errorCode = e.getErrorCode();
        var body = BaseResponse.error(
            errorCode.getStatus(),
            errorCode.name(),
            errorCode.getMessage(),
            null
        );

        log.warn("Business Exception Occurred: Code={}, Message={}", errorCode.name(),
            errorCode.getMessage());
        return ResponseEntity.status(body.status()).body(body);
    }

    /* 2) 권한 위반 */
    @ExceptionHandler(AccessDeniedException.class)
    protected ResponseEntity<BaseResponse<Object>> handleAccessDeniedException(
        AccessDeniedException e) {
        ErrorCode errorCode = ErrorCode.PERMISSION_DENIED;
        var body = BaseResponse.error(
            errorCode.getStatus(),
            errorCode.name(),
            errorCode.getMessage(),
            null
        );

        return ResponseEntity.status(body.status()).body(body);
    }

    /* 3) @Valid / @Validated 바인딩 오류 */
    @ExceptionHandler(MethodArgumentNotValidException.class)
    protected ResponseEntity<BaseResponse<Map<String, String>>> handleValidationException(
        MethodArgumentNotValidException e) {

        Map<String, String> details = e.getBindingResult().getFieldErrors().stream()
            .collect(Collectors.toMap(FieldError::getField, FieldError::getDefaultMessage));

        var body = BaseResponse.error(
            ErrorCode.VALIDATION_FAILED.getStatus(),
            "VALIDATION_ERROR",
            "요청 파라미터가 유효하지 않습니다.",
            details
        );

        log.warn("Validation failed: {}", details);
        return ResponseEntity.status(body.status()).body(body);
    }

    /* 4) 파라미터 제약 조건(@Size 등) 위반 */
    @ExceptionHandler(ConstraintViolationException.class)
    protected ResponseEntity<BaseResponse<Map<String, String>>> handleConstraintViolation(
        ConstraintViolationException e) {

        Map<String, String> details = e.getConstraintViolations().stream()
            .collect(Collectors.toMap(
                violation -> violation.getPropertyPath().toString(),
                ConstraintViolation::getMessage
            ));

        var body = BaseResponse.error(
            ErrorCode.VALIDATION_FAILED.getStatus(),
            "VALIDATION_ERROR",
            "요청 파라미터가 유효하지 않습니다.",
            details
        );

        log.warn("Constraint validation failed: {}", details);
        return ResponseEntity.status(body.status()).body(body);
    }

    /* 5) SSE/비동기 스트리밍 중 클라이언트 연결 종료 예외 */
    @ExceptionHandler({
        AsyncRequestNotUsableException.class,
        ClientAbortException.class
    })
    protected void handleClientDisconnection(Exception e) {
        // 클라이언트가 연결을 끊은 것은 정상적인 시나리오이므로 DEBUG 레벨로만 로깅
        Throwable cause = e.getCause();
        if (cause instanceof java.io.IOException &&
            (cause.getMessage() != null && cause.getMessage()
                .contains("Connection reset by peer"))) {
            log.debug("Client disconnected during streaming: {}", cause.getMessage());
        } else {
            log.debug("Client disconnected during async request: {}", e.getMessage());
        }
        // 응답을 반환하지 않고 조용히 처리
    }

    /* 6) SSE 스트리밍 중 발생하는 메시지 변환 예외 */
    @ExceptionHandler(HttpMessageNotWritableException.class)
    protected void handleHttpMessageNotWritableException(HttpMessageNotWritableException e) {
        // text/event-stream Content-Type이 이미 설정된 상태에서 BaseResponse를 변환할 수 없는 경우
        // 이는 예외 처리 중 발생하는 이차 예외이므로 DEBUG 레벨로만 로깅
        if (e.getMessage() != null && e.getMessage().contains("text/event-stream")) {
            log.debug("SSE stream already closed, cannot write error response: {}", e.getMessage());
        } else {
            log.warn("HTTP message not writable: {}", e.getMessage());
        }
        // 응답을 반환하지 않고 조용히 처리
    }

    /* 7) 그밖의 모든 예외 */
    @ExceptionHandler(Exception.class)
    protected ResponseEntity<BaseResponse<Object>> handleException(Exception e) {
        // 클라이언트 연결 종료 관련 예외는 이미 위에서 처리되었으므로 여기서는 건너뛰기
        if (e.getCause() instanceof ClientAbortException ||
            e.getCause() instanceof java.io.IOException &&
                e.getCause().getMessage() != null &&
                e.getCause().getMessage().contains("Connection reset by peer")) {
            log.debug("Client disconnection detected in general handler: {}", e.getMessage());
            return null; // 응답을 반환하지 않음
        }

        ErrorCode error = ErrorCode.INTERNAL_SERVER_ERROR;
        var body = BaseResponse.error(error.getStatus(), error.name(), error.getMessage(), null);

        log.error("Unhandled exception", e);
        return ResponseEntity.status(body.status()).body(body);
    }
}
