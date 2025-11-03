package com.ssafy.hebees.domain.offer.entity;

import com.ssafy.hebees.global.entity.BaseEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Entity
@Table(name = "OFFER")
@Getter
@Builder(toBuilder = true)
@AllArgsConstructor(access = AccessLevel.PRIVATE)
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class Offer extends BaseEntity {

    @Id
    @Column(name = "OFFER_NO", columnDefinition = "CHAR(10)", nullable = false)
    private String offerNo;  // 사업자 번호를 PK로 사용

    @Column(name = "VERSION", nullable = false)
    private Integer version;
}
