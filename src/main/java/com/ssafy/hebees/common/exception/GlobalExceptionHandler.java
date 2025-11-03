package com.ssafy.hebees.common.exception;

import com.ssafy.hebees.common.response.BaseResponse;
import io.swagger.v3.oas.annotations.Hidden;
import jakarta.validation.ConstraintViolation;
import jakarta.validation.ConstraintViolationException;
import java.util.Map;
import java.util.stream.Collectors;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

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

    /* 5) 그밖의 모든 예외 */
    @ExceptionHandler(Exception.class)
    protected ResponseEntity<BaseResponse<Object>> handleException(Exception e) {
        ErrorCode error = ErrorCode.INTERNAL_SERVER_ERROR;
        var body = BaseResponse.error(error.getStatus(), error.name(), error.getMessage(), null);

        log.error("Unhandled exception", e);
        return ResponseEntity.status(body.status()).body(body);
    }
}
