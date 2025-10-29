package com.ssafy.hebees.user.repository;

import com.ssafy.hebees.user.entity.UserRole;

import java.util.Optional;

/**
 * QueryDSL을 사용한 UserRole 커스텀 Repository 인터페이스
 */
public interface UserRoleRepositoryCustom {

    /**
     * 역할명으로 UserRole 조회 (QueryDSL)
     *
     * @param name 역할명
     * @return UserRole 정보 (Optional)
     */
    Optional<UserRole> findByNameWithQueryDSL(String name);

    /**
     * 역할명 존재 여부 확인 (QueryDSL)
     *
     * @param name 역할명
     * @return 존재 여부
     */
    boolean existsByNameWithQueryDSL(String name);
}
