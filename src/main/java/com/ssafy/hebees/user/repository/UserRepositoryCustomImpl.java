package com.ssafy.hebees.user.repository;

import com.querydsl.jpa.impl.JPAQueryFactory;
import com.ssafy.hebees.user.entity.QUser;
import com.ssafy.hebees.user.entity.User;
import com.ssafy.hebees.user.entity.UserRole;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
@RequiredArgsConstructor
public class UserRepositoryCustomImpl implements UserRepositoryCustom {

    private final JPAQueryFactory queryFactory;
    private final QUser user = QUser.user;

    @Override
    public List<User> findByRole(UserRole role) {
        return queryFactory
            .selectFrom(user)
            .where(user.role.eq(role)
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
    public Optional<User> findByUserNameWithQueryDSL(String userName) {
        User result = queryFactory
            .selectFrom(user)
            .where(user.userName.eq(userName)
                .and(user.deletedAt.isNull()))
            .fetchOne();

        return Optional.ofNullable(result);
    }

    @Override
    public Optional<User> findByUserIdWithQueryDSL(String userId) {
        User result = queryFactory
            .selectFrom(user)
            .where(user.userId.eq(userId)
                .and(user.deletedAt.isNull()))
            .fetchOne();

        return Optional.ofNullable(result);
    }
}
