package com.ssafy.hebees.user.repository;

import com.querydsl.jpa.impl.JPAQueryFactory;
import com.ssafy.hebees.user.entity.QUser;
import com.ssafy.hebees.user.entity.QUserRole;
import com.ssafy.hebees.user.entity.User;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
@RequiredArgsConstructor
public class UserRepositoryCustomImpl implements UserRepositoryCustom {

    private final JPAQueryFactory queryFactory;
    private final QUser user = QUser.user;
    private final QUserRole userRole = QUserRole.userRole;

    @Override
    public List<User> findByRoleName(String roleName) {
        return queryFactory
            .selectFrom(user)
            .join(user.userRole, userRole)
            .where(userRole.name.eq(roleName)
                .and(user.deletedAt.isNull()))
            .fetch();
    }

    @Override
    public long countActiveUsers() {
        Long count = queryFactory
            .select(user.count())
            .from(user)
            .where(user.deletedAt.isNull())
            .fetchOne();

        return count != null ? count : 0L;
    }

    @Override
    public Optional<User> findByEmailWithQueryDSL(String email) {
        User result = queryFactory
            .selectFrom(user)
            .where(user.email.eq(email)
                .and(user.deletedAt.isNull()))
            .fetchOne();

        return Optional.ofNullable(result);
    }

    @Override
    public Optional<User> findByNameWithQueryDSL(String name) {
        User result = queryFactory
            .selectFrom(user)
            .where(user.name.eq(name)
                .and(user.deletedAt.isNull()))
            .fetchOne();

        return Optional.ofNullable(result);
    }

    @Override
    public boolean existsByRoleUuid(UUID userRoleUuid) {
        Integer result = queryFactory
            .selectOne()
            .from(user)
            .join(user.userRole, userRole)
            .where(userRole.uuid.eq(userRoleUuid)
                .and(user.deletedAt.isNull()))
            .fetchFirst();

        return result != null;
    }
}
