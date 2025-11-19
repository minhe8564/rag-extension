package com.ssafy.hebees.user.repository;

import com.ssafy.hebees.user.entity.User;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.UUID;

@Repository
public interface UserRepository extends JpaRepository<User, UUID>, UserRepositoryCustom {

    @EntityGraph(attributePaths = {"userRole", "offer"})
    Page<User> findByDeletedAtIsNull(Pageable pageable);

    long countByDeletedAtIsNull();

    @EntityGraph(attributePaths = {"userRole", "offer"})
    java.util.Optional<User> findByUuid(UUID uuid);
}
