package com.ssafy.hebees.common.exception;

import lombok.Getter;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;

@Getter
@RequiredArgsConstructor
public enum ErrorCode {

    INVALID_TOKEN(HttpStatus.UNAUTHORIZED, "토큰을 찾을 수 없거나 형식이 잘못됨"),
    INVALID_ACCESS_TOKEN(HttpStatus.UNAUTHORIZED, "유효하지 않은 액세스 토큰"),
    INVALID_REFRESH_TOKEN(HttpStatus.UNAUTHORIZED, "유효하지 않은 리프레시 토큰"),
    INVALID_SIGNIN(HttpStatus.BAD_REQUEST, "존재하지 않는 사용자 또는 비밀번호 불일치"),
    INVALID_PASSWORD(HttpStatus.BAD_REQUEST, "비밀번호 불일치"),
    INVALID_INPUT(HttpStatus.BAD_REQUEST, "잘못된 입력값"),
    INVALID_FILE_NAME(HttpStatus.BAD_REQUEST, "잘못된 파일명"),
    ALREADY_EXISTS(HttpStatus.CONFLICT, "이미 존재하는 데이터"),
    NOT_FOUND(HttpStatus.NOT_FOUND, "대상 데이터를 찾을 수 없음"),
    BAD_REQUEST(HttpStatus.BAD_REQUEST, "올바르지 않은 요청"),
    VALIDATION_FAILED(HttpStatus.BAD_REQUEST, "유효성 검사에 실패"),
    PERMISSION_DENIED(HttpStatus.FORBIDDEN, "권한 부족"),
    INTERNAL_SERVER_ERROR(HttpStatus.INTERNAL_SERVER_ERROR, "서버 내부 오류 발생");

    private final HttpStatus status;
    private final String message;
}
