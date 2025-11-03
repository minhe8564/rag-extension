package com.ssafy.hebees.user.repository;

import com.ssafy.hebees.user.entity.User;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

/**
 * QueryDSL을 사용한 커스텀 Repository 인터페이스
 */
public interface UserRepositoryCustom {

    /**
     * 역할명으로 사용자 조회
     *
     * @param roleName 사용자 역할명
     * @return 해당 역할의 사용자 목록
     */
    List<User> findByRoleName(String roleName);

    /**
     * 활성 사용자 수 조회
     *
     * @return 활성 사용자 수
     */
    long countActiveUsers();

    /**
     * 이메일로 사용자 조회 (QueryDSL)
     *
     * @param email 사용자 이메일
     * @return 사용자 정보 (Optional)
     */
    Optional<User> findByEmailWithQueryDSL(String email);

    /**
     * 사용자명으로 사용자 조회 (QueryDSL)
     *
     * @param name 사용자명
     * @return 사용자 정보 (Optional)
     */
    Optional<User> findByNameWithQueryDSL(String name);

    /**
     * 특정 역할을 사용하는 사용자가 존재하는지 확인 (QueryDSL)
     *
     * @param userRoleUuid 역할 UUID
     * @return 해당 역할을 사용하는 사용자의 존재 여부
     */
    boolean existsByRoleUuid(UUID userRoleUuid);
}
