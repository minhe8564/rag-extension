package com.ssafy.hebees.user.service;

import com.ssafy.hebees.user.dto.UserSignupRequest;
import com.ssafy.hebees.user.dto.UserSignupResponse;
import com.ssafy.hebees.user.entity.User;
import com.ssafy.hebees.user.entity.UserRole;

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
     * 사용자 ID로 사용자 조회
     *
     * @param userId 사용자 ID
     * @return 사용자 정보
     */
    User findByUserId(String userId);

    /**
     * 사용자명으로 사용자 조회
     *
     * @param userName 사용자명
     * @return 사용자 정보
     */
    User findByUserName(String userName);

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
     * @param userName 확인할 사용자명
     * @return 중복 여부
     */
    boolean isUserNameExists(String userName);

    /**
     * 사용자 ID 중복 확인
     *
     * @param userId 확인할 사용자 ID
     * @return 중복 여부
     */
    boolean isUserIdExists(String userId);

    /**
     * 역할별 사용자 조회
     *
     * @param role 사용자 역할
     * @return 해당 역할의 사용자 목록
     */
    List<User> findUsersByRole(UserRole role);

    /**
     * 활성 사용자 수 조회
     *
     * @return 활성 사용자 수
     */
    long getActiveUserCount();
}