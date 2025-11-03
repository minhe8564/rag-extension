package com.ssafy.hebees.domain.offer.repository;

import com.querydsl.jpa.impl.JPAQueryFactory;
import com.ssafy.hebees.domain.offer.entity.QOffer;
import com.ssafy.hebees.domain.offer.entity.Offer;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
@RequiredArgsConstructor
public class OfferRepositoryCustomImpl implements OfferRepositoryCustom {

    private final JPAQueryFactory queryFactory;
    private final QOffer offer = QOffer.offer;

    @Override
    public Optional<Offer> findByBusinessNoWithQueryDSL(String businessNo) {
        Offer result = queryFactory
            .selectFrom(offer)
            .where(offer.offerNo.eq(businessNo))
            .fetchOne();

        return Optional.ofNullable(result);
    }

    @Override
    public boolean existsByBusinessNoWithQueryDSL(String businessNo) {
        Long count = queryFactory
            .select(offer.count())
            .from(offer)
            .where(offer.offerNo.eq(businessNo))
            .fetchOne();

        return count != null && count > 0;
    }
}

