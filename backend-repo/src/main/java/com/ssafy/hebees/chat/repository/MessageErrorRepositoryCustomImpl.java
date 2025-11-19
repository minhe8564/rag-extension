package com.ssafy.hebees.chat.repository;

import com.querydsl.core.types.dsl.BooleanExpression;
import com.querydsl.jpa.impl.JPAQueryFactory;
import com.ssafy.hebees.chat.entity.MessageError;
import com.ssafy.hebees.chat.entity.QMessageError;
import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Repository;

@Repository
@RequiredArgsConstructor
public class MessageErrorRepositoryCustomImpl implements MessageErrorRepositoryCustom {

    private final JPAQueryFactory queryFactory;
    private static final QMessageError messageError = QMessageError.messageError;

    @Override
    public Page<MessageError> search(UUID sessionNo, UUID userNo, Pageable pageable) {
        List<MessageError> content = queryFactory
            .selectFrom(messageError)
            .where(
                eqSessionNo(sessionNo),
                eqUserNo(userNo)
            )
            .orderBy(messageError.createdAt.desc())
            .offset(pageable.getOffset())
            .limit(pageable.getPageSize())
            .fetch();

        Long total = queryFactory
            .select(messageError.count())
            .from(messageError)
            .where(
                eqSessionNo(sessionNo),
                eqUserNo(userNo)
            )
            .fetchOne();

        long totalCount = total != null ? total : 0L;

        return new PageImpl<>(content, pageable, totalCount);
    }

    @Override
    public List<MessageError> findByCreatedAtBetweenOrderByCreatedAtDesc(
        LocalDateTime startInclusive, LocalDateTime endExclusive, int limit) {
        return queryFactory.selectFrom(messageError)
            .where(messageError.createdAt.between(startInclusive, endExclusive))
            .orderBy(messageError.createdAt.desc())
            .limit(limit)
            .fetch();
    }

    private BooleanExpression eqSessionNo(UUID sessionNo) {
        if (sessionNo == null) {
            return null;
        }
        return messageError.sessionNo.eq(sessionNo);
    }

    private BooleanExpression eqUserNo(UUID userNo) {
        if (userNo == null) {
            return null;
        }
        return messageError.userNo.eq(userNo);
    }
}

