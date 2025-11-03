package com.ssafy.hebees.domain.user.repository;

import com.querydsl.jpa.impl.JPAQueryFactory;
import com.ssafy.hebees.domain.user.entity.QUserRole;
import com.ssafy.hebees.domain.user.entity.UserRole;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
@RequiredArgsConstructor
public class UserRoleRepositoryCustomImpl implements UserRoleRepositoryCustom {

    private final JPAQueryFactory queryFactory;
    private final QUserRole userRole = QUserRole.userRole;

    @Override
    public Optional<UserRole> findByNameWithQueryDSL(String name) {
        UserRole result = queryFactory
            .selectFrom(userRole)
            .where(userRole.name.eq(name))
            .fetchOne();

        return Optional.ofNullable(result);
    }

    @Override
    public boolean existsByNameWithQueryDSL(String name) {
        Long count = queryFactory
            .select(userRole.count())
            .from(userRole)
            .where(userRole.name.eq(name))
            .fetchOne();

        return count != null && count > 0;
    }
}
