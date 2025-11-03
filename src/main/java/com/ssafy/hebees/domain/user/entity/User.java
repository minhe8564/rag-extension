package com.ssafy.hebees.domain.user.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.ssafy.hebees.global.entity.BaseSoftDeleteEntity;
import com.ssafy.hebees.domain.offer.entity.Offer;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.PrePersist;
import jakarta.persistence.Table;
import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.SQLDelete;

import java.util.UUID;

@Entity
@Table(name = "USER")
@Getter
@Builder(toBuilder = true)
@AllArgsConstructor(access = AccessLevel.PRIVATE)
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@SQLDelete(sql = "UPDATE USER SET DELETED_AT = CURRENT_TIMESTAMP WHERE USER_NO = ?")
public class User extends BaseSoftDeleteEntity {

    @Id
    @Column(name = "USER_NO", columnDefinition = "BINARY(16)", nullable = false)
    private UUID uuid;

    @PrePersist
    protected void generateUuid() {
        if (uuid == null) {
            uuid = UUID.randomUUID();
        }
    }

    @Column(name = "EMAIL", nullable = false, length = 254, unique = true)
    private String email;

    @JsonIgnore
    @Column(name = "PASSWORD", nullable = false, length = 255)
    private String password;

    @Column(name = "NAME", nullable = false, length = 50)
    private String name;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "USER_ROLE_NO", nullable = false)
    private UserRole userRole;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "OFFER_NO", nullable = false)
    private Offer offer;

    // 0 : 개인 안경원, 1 : 체인 안경원, 2 : 제조 유통사
    @Column(name = "BUSINESS_TYPE", nullable = false)
    private int businessType;

    public String getRoleName() {
        return userRole != null ? userRole.getName() : null;
    }
}
