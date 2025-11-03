package com.ssafy.hebees.global.exception;

import lombok.Getter;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;

@Getter
@RequiredArgsConstructor
public enum ErrorCode {

    // 인증 관련 (401)
    INVALID_TOKEN(HttpStatus.UNAUTHORIZED, "유효하지 않은 토큰 형식입니다"),
    INVALID_ACCESS_TOKEN(HttpStatus.UNAUTHORIZED, "유효하지 않은 액세스 토큰입니다"),
    INVALID_REFRESH_TOKEN(HttpStatus.UNAUTHORIZED, "유효하지 않은 리프레시 토큰입니다"),
    INVALID_SIGNIN(HttpStatus.UNAUTHORIZED, "아이디와 비밀번호가 일치하지 않습니다"),
    UNAUTHORIZED(HttpStatus.UNAUTHORIZED, "인증이 필요합니다"),

    // 인가 관련 (403)
    PERMISSION_DENIED(HttpStatus.FORBIDDEN, "접근 권한이 없습니다"),

    // 요청 오류 (400)
    BAD_REQUEST(HttpStatus.BAD_REQUEST, "잘못된 요청입니다"),
    INVALID_INPUT(HttpStatus.BAD_REQUEST, "잘못된 입력값입니다"),
    INVALID_PASSWORD(HttpStatus.BAD_REQUEST, "비밀번호가 일치하지 않습니다"),
    INVALID_FILE_NAME(HttpStatus.BAD_REQUEST, "잘못된 파일명입니다"),
    VALIDATION_FAILED(HttpStatus.BAD_REQUEST, "유효성 검증에 실패했습니다"),

    // 중복 / 상태 충돌 (409)
    ALREADY_EXISTS(HttpStatus.CONFLICT, "이미 존재하는 데이터입니다"),
    USER_ROLE_IN_USE(HttpStatus.CONFLICT, "사용 중인 사용자 역할은 삭제할 수 없습니다"),

    // 리소스 없음 (404)
    NOT_FOUND(HttpStatus.NOT_FOUND, "대상 데이터를 찾을 수 없습니다"),
    USER_ROLE_NOT_FOUND(HttpStatus.NOT_FOUND, "사용자 역할을 찾을 수 없습니다"),
    OFFER_NOT_FOUND(HttpStatus.NOT_FOUND, "가맹점 정보를 찾을 수 없습니다"),

    // 서버 오류 (500)
    INTERNAL_SERVER_ERROR(HttpStatus.INTERNAL_SERVER_ERROR, "서버 내부 오류가 발생했습니다");

    private final HttpStatus status;
    private final String message;
}





