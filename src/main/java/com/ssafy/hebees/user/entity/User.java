package com.ssafy.hebees.user.entity;

import com.ssafy.hebees.common.entity.BaseSoftDeleteEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.PrePersist;
import jakarta.persistence.Table;
import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.SQLDelete;
@Entity
@Table(name = "users")
@Getter
@Builder(toBuilder = true)
@AllArgsConstructor(access = AccessLevel.PRIVATE)
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@SQLDelete(sql = "UPDATE users SET deleted_at = CURRENT_TIMESTAMP WHERE uuid = ?")
public class User extends BaseSoftDeleteEntity {

    @Column(name = "user_id", nullable = false, unique = true, length = 7)
    private String userId;

    @Column(nullable = false, length = 100)
    private String password;

    @Column(name = "user_name", nullable = false, length = 20)
    private String userName;

    @Enumerated(EnumType.STRING)
    @Column(name = "user_role", nullable = false)
    private UserRole role;

    @PrePersist
    void applyDefaults() {
        if (this.role == null) {
            this.role = UserRole.ADMIN;
        }
    }
}
