package com.ssafy.hebees.domain.offer.repository;

import com.ssafy.hebees.domain.offer.entity.Offer;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface OfferRepository extends JpaRepository<Offer, String>, OfferRepositoryCustom {

}
