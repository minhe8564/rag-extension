package com.ssafy.hebees.user.repository;

import com.ssafy.hebees.user.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;
import java.util.UUID;

@Repository
public interface UserRepository extends JpaRepository<User, UUID>, UserRepositoryCustom {

    /**
     * 사용자 ID로 사용자 조회
     *
     * @param userId 사용자 ID
     * @return 사용자 정보 (Optional)
     */
    Optional<User> findByUserId(String userId);

    /**
     * 사용자 ID 중복 확인
     *
     * @param userId 사용자 ID
     * @return 사용자 ID 존재 여부
     */
    boolean existsByUserId(String userId);

    /**
     * 사용자명으로 사용자 조회
     *
     * @param userName 사용자명
     * @return 사용자 정보 (Optional)
     */
    Optional<User> findByUserName(String userName);

    /**
     * 사용자명 중복 확인
     *
     * @param userName 사용자명
     * @return 사용자명 존재 여부
     */
    boolean existsByUserName(String userName);
}
