package com.ssafy.hebees.common.entity;

import jakarta.persistence.Column;
import jakarta.persistence.MappedSuperclass;
import java.time.LocalDateTime;
import lombok.Getter;
import org.hibernate.annotations.SQLRestriction;

@Getter
@MappedSuperclass
@SQLRestriction("deleted_at IS NULL")
public abstract class BaseSoftDeleteEntity extends BaseEntity {

    @Column(name = "DELETED_AT")
    private LocalDateTime deletedAt;
}
