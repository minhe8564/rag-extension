package com.ssafy.hebees.domain.user.service;

import com.ssafy.hebees.domain.user.dto.request.UserSignupRequest;
import com.ssafy.hebees.domain.user.dto.response.UserSignupResponse;
import com.ssafy.hebees.domain.user.entity.User;

import java.util.List;
import java.util.UUID;

/**
 * 사용자 서비스 인터페이스
 */
public interface UserService {

    /**
     * 회원가입
     *
     * @param request 회원가입 요청 정보
     * @return 회원가입된 사용자 정보
     */
    UserSignupResponse signup(UserSignupRequest request);

    /**
     * 이메일로 사용자 조회
     *
     * @param email 사용자 이메일
     * @return 사용자 정보
     */
    User findByEmail(String email);

    /**
     * 사용자명으로 사용자 조회
     *
     * @param name 사용자명
     * @return 사용자 정보
     */
    User findByName(String name);

    /**
     * UUID로 사용자 조회
     *
     * @param userUuid 사용자 UUID
     * @return 사용자 정보
     */
    User findByUuid(UUID userUuid);

    /**
     * 사용자명 중복 확인
     *
     * @param name 확인할 사용자명
     * @return 중복 여부
     */
    boolean isNameExists(String name);

    /**
     * 이메일 중복 확인
     *
     * @param email 확인할 이메일
     * @return 중복 여부
     */
    boolean isEmailExists(String email);

    /**
     * 역할별 사용자 조회
     *
     * @param roleName 사용자 역할명
     * @return 해당 역할의 사용자 목록
     */
    List<User> findUsersByRoleName(String roleName);

    /**
     * 활성 사용자 수 조회
     *
     * @return 활성 사용자 수
     */
    long getActiveUserCount();
}
