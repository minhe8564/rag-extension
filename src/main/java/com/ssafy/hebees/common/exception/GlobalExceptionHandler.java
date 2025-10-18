package com.ssafy.hebees.common.exception;

import io.swagger.v3.oas.annotations.Hidden;
import jakarta.validation.ConstraintViolation;
import jakarta.validation.ConstraintViolationException;
import java.util.Map;
import java.util.stream.Collectors;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.security.authorization.AuthorizationDeniedException;
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
    protected ResponseEntity<ErrorResponse> handleBusinessException(BusinessException e) {
        ErrorCode errorCode = e.getErrorCode();
        ErrorResponse errorResponse = ErrorResponse.of(errorCode);

        log.warn("Business Exception Occurred: Code={}, Message={}", errorCode.name(),
            errorCode.getMessage());
        return ResponseEntity.status(errorResponse.status()).body(errorResponse);
    }

    /* 2) 권한 위반 */
    @ExceptionHandler(AccessDeniedException.class)
    protected ResponseEntity<ErrorResponse> handleAccessDeniedException(AccessDeniedException e) {
        ErrorCode errorCode = ErrorCode.PERMISSION_DENIED;
        ErrorResponse errorResponse = ErrorResponse.of(errorCode);

        return ResponseEntity.status(errorResponse.status()).body(errorResponse);
    }

    /* 3) @Valid / @Validated 바인딩 오류 */
    @ExceptionHandler(MethodArgumentNotValidException.class)
    protected ResponseEntity<ErrorResponse> handleValidationException(
        MethodArgumentNotValidException e) {

        Map<String, String> details = e.getBindingResult().getFieldErrors().stream()
            .collect(Collectors.toMap(FieldError::getField, FieldError::getDefaultMessage));
        ErrorResponse errorResponse = ErrorResponse.of(ErrorCode.VALIDATION_FAILED, details);

        log.warn("Validation failed: {}", details);
        return ResponseEntity.status(errorResponse.status()).body(errorResponse);
    }

    /* 4) 파라미터 제약 조건(@Size 등) 위반 */
    @ExceptionHandler(ConstraintViolationException.class)
    protected ResponseEntity<ErrorResponse> handleConstraintViolation(
        ConstraintViolationException e) {

        Map<String, String> details = e.getConstraintViolations().stream()
            .collect(Collectors.toMap(
                violation -> violation.getPropertyPath().toString(),
                ConstraintViolation::getMessage
            ));
        ErrorResponse errorResponse = ErrorResponse.of(ErrorCode.VALIDATION_FAILED, details);

        log.warn("Constraint validation failed: {}", details);
        return ResponseEntity.status(errorResponse.status()).body(errorResponse);
    }

    /* 5) 그밖의 모든 예외 */
    @ExceptionHandler(Exception.class)
    protected ResponseEntity<ErrorResponse> handleException(Exception e) {
        ErrorResponse errorResponse = ErrorResponse.of(ErrorCode.INTERNAL_SERVER_ERROR);

        log.error("Unhandled exception", e);
        return ResponseEntity.status(errorResponse.status()).body(errorResponse);
    }
}
