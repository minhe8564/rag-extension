package com.ssafy.hebees.domain.offer.repository;

import com.ssafy.hebees.domain.offer.entity.Offer;

import java.util.Optional;

/**
 * QueryDSL을 사용한 Offer 커스텀 Repository 인터페이스
 */
public interface OfferRepositoryCustom {

    /**
     * 사업자 번호(OFFER_NO)로 Offer 조회 (QueryDSL)
     *
     * @param businessNo 사업자 번호 (CHAR(10))
     * @return Offer 정보 (Optional)
     */
    Optional<Offer> findByBusinessNoWithQueryDSL(String businessNo);

    /**
     * 사업자 번호(OFFER_NO) 존재 여부 확인 (QueryDSL)
     *
     * @param businessNo 사업자 번호 (CHAR(10))
     * @return 존재 여부
     */
    boolean existsByBusinessNoWithQueryDSL(String businessNo);
}

