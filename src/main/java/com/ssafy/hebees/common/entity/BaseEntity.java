package com.ssafy.hebees.common.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Id;
import jakarta.persistence.MappedSuperclass;
import java.util.UUID;
import lombok.Getter;

@Getter
@MappedSuperclass
public abstract class BaseEntity {

    @Id
    @Column(name = "uuid", updatable = false, nullable = false)
    private UUID uuid = UUID.randomUUID();
}
