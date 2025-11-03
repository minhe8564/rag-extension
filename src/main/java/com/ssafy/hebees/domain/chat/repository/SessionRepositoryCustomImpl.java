package com.ssafy.hebees.domain.chat.repository;

import com.querydsl.core.types.dsl.BooleanExpression;
import com.querydsl.jpa.impl.JPAQueryFactory;
import com.ssafy.hebees.domain.chat.entity.QSession;
import com.ssafy.hebees.domain.chat.entity.Session;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

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

    private BooleanExpression eqTitleIgnoreCase(String title) {
        if (title == null || title.isBlank()) {
            return null;
        }
        return session.title.equalsIgnoreCase(title.trim());
    }
}


