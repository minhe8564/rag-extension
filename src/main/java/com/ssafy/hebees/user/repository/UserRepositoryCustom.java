package com.ssafy.hebees.user.repository;

import com.ssafy.hebees.user.entity.User;
import com.ssafy.hebees.user.entity.UserRole;

import java.util.List;

/**
 * QueryDSL을 사용한 커스텀 Repository 인터페이스
 */
public interface UserRepositoryCustom {

    /**
     * 역할별 사용자 조회
     *
     * @param role 사용자 역할
     * @return 해당 역할의 사용자 목록
     */
    List<User> findByRole(UserRole role);

    /**
     * 활성 사용자 수 조회
     *
     * @return 활성 사용자 수
     */
    long countActiveUsers();

    /**
     * 사용자명으로 사용자 조회 (QueryDSL)
     *
     * @param userName 사용자명
     * @return 사용자 정보 (Optional)
     */
    java.util.Optional<User> findByUserNameWithQueryDSL(String userName);

    /**
     * 사용자 ID로 사용자 조회 (QueryDSL)
     *
     * @param userId 사용자 ID
     * @return 사용자 정보 (Optional)
     */
    java.util.Optional<User> findByUserIdWithQueryDSL(String userId);
}
