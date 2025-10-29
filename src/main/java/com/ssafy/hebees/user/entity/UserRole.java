package com.ssafy.hebees.user.entity;

import com.ssafy.hebees.common.entity.BaseEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.Id;
import jakarta.persistence.OneToMany;
import jakarta.persistence.PrePersist;
import jakarta.persistence.Table;
import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

@Entity
@Table(name = "USER_ROLE")
@Getter
@Builder(toBuilder = true)
@AllArgsConstructor(access = AccessLevel.PRIVATE)
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class UserRole extends BaseEntity {

    @Id
    @Column(name = "USER_ROLE_NO", columnDefinition = "BINARY(16)", nullable = false)
    private UUID uuid;

    @PrePersist
    protected void generateUuid() {
        if (uuid == null) {
            uuid = UUID.randomUUID();
        }
    }

    @Column(name = "NAME", nullable = false, length = 20, unique = true)
    private String name;

    @Column(name = "MODE", nullable = false)
    private Integer mode;

    @OneToMany(mappedBy = "userRole", fetch = FetchType.LAZY)
    @Builder.Default
    private List<User> users = new ArrayList<>();
}

