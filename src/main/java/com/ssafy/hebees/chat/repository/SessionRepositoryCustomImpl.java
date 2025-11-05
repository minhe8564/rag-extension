package com.ssafy.hebees.chat.repository;

import com.querydsl.core.types.dsl.BooleanExpression;
import com.querydsl.jpa.impl.JPAQuery;
import com.querydsl.jpa.impl.JPAQueryFactory;
import com.ssafy.hebees.chat.entity.QSession;
import com.ssafy.hebees.chat.entity.Session;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Repository;

@Repository
@RequiredArgsConstructor
public class SessionRepositoryCustomImpl implements SessionRepositoryCustom {

    private final JPAQueryFactory queryFactory;
    private static final QSession session = QSession.session;

    @Override
    public Optional<Session> findBySessionNo(UUID sessionNo) {
        Session result = queryFactory
            .selectFrom(session)
            .where(eqSessionNo(sessionNo))
            .fetchOne();

        return Optional.ofNullable(result);
    }

    @Override
    public boolean existsByUserNoAndTitleIgnoreCase(UUID userNo, String title) {
        if (userNo == null || title == null || title.isBlank()) {
            return false;
        }

        Integer exists = queryFactory
            .selectOne()
            .from(session)
            .where(
                eqUserNo(userNo),
                eqTitleIgnoreCase(title)
            )
            .fetchFirst();

        return exists != null;
    }

    @Override
    public Page<Session> searchSessionsByUser(UUID userNo, String keyword, Pageable pageable) {
        List<Session> content = queryFactory
            .selectFrom(session)
            .where(
                eqUserNo(userNo),
                containsKeyword(keyword)
            )
            .orderBy(session.updatedAt.desc(), session.title.asc())
            .offset(pageable.getOffset())
            .limit(pageable.getPageSize())
            .fetch();

        Long total = queryFactory
            .select(session.count())
            .from(session)
            .where(
                eqUserNo(userNo),
                containsKeyword(keyword)
            )
            .fetchOne();

        long totalCount = total != null ? total : 0L;

        return new PageImpl<>(content, pageable, totalCount);
    }

    @Override
    public List<Session> findCreatedBetween(LocalDateTime startInclusive,
        LocalDateTime endExclusive,
        int limit) {
        if (startInclusive == null || endExclusive == null) {
            return List.of();
        }

        JPAQuery<Session> query = queryFactory
            .selectFrom(session)
            .where(
                createdAtGoe(startInclusive),
                createdAtLt(endExclusive)
            )
            .orderBy(session.createdAt.desc());

        if (limit > 0) {
            query.limit(limit);
        }

        return query.fetch();
    }

    private BooleanExpression eqSessionNo(UUID sessionNo) {
        if (sessionNo == null) {
            return null;
        }
        return session.sessionNo.eq(sessionNo);
    }

    private BooleanExpression eqUserNo(UUID userNo) {
        if (userNo == null) {
            return null;
        }
        return session.userNo.eq(userNo);
    }

    private BooleanExpression containsKeyword(String keyword) {
        if (keyword == null || keyword.isBlank()) {
            return null;
        }
        return session.title.containsIgnoreCase(keyword.trim());
    }

    private BooleanExpression createdAtGoe(LocalDateTime startInclusive) {
        if (startInclusive == null) {
            return null;
        }
        return session.createdAt.goe(startInclusive);
    }

    private BooleanExpression createdAtLt(LocalDateTime endExclusive) {
        if (endExclusive == null) {
            return null;
        }
        return session.createdAt.lt(endExclusive);
    }

    private BooleanExpression eqTitleIgnoreCase(String title) {
        if (title == null || title.isBlank()) {
            return null;
        }
        return session.title.equalsIgnoreCase(title.trim());
    }
}


