package com.ssafy.hebees.domain.user.repository;

import com.ssafy.hebees.domain.user.entity.UserRole;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.UUID;

@Repository
public interface UserRoleRepository extends JpaRepository<UserRole, UUID>,
    UserRoleRepositoryCustom {
    // QueryDSL을 사용한 커스텀 메서드는 UserRoleRepositoryCustom에서 정의
}
