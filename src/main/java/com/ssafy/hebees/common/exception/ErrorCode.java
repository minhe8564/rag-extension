package com.ssafy.hebees.common.exception;

import lombok.Getter;
import lombok.RequiredArgsConstructor;

@Getter
@RequiredArgsConstructor
public enum ErrorCode {

    INVALID_TOKEN(401, "토큰을 찾을 수 없거나 형식이 잘못됨"),
    INVALID_ACCESS_TOKEN(401, "유효하지 않은 액세스 토큰"),
    INVALID_REFRESH_TOKEN(401, "유효하지 않은 리프레시 토큰"),
    INVALID_SIGNIN(400, "존재하지 않는 사용자 또는 비밀번호 불일치"),
    INVALID_PASSWORD(400, "비밀번호 불일치"),
    INVALID_INPUT(400, "잘못된 입력값"),
    INVALID_FILE_NAME(400, "잘못된 파일명"),
    ALREADY_EXISTS(409, "이미 존재하는 데이터"),
    NOT_FOUND(404, "대상 데이터를 찾을 수 없음"),
    BAD_REQUEST(400, "올바르지 않은 요청"),
    VALIDATION_FAILED(400, "유효성 검사에 실패"),
    PERMISSION_DENIED(403, "권한 부족"),
    INTERNAL_SERVER_ERROR(500, "서버 내부 오류 발생");

    private final int status;
    private final String message;
}
