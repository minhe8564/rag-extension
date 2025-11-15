package com.ssafy.hebees.monitoring.entity;

import com.ssafy.hebees.common.entity.BaseEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.PrePersist;
import jakarta.persistence.Table;
import java.util.UUID;
import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Entity
@Table(name = "RUNPOD")
@Getter
@Builder(toBuilder = true)
@AllArgsConstructor(access = AccessLevel.PRIVATE)
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class Runpod extends BaseEntity {

    @Id
    @Column(name = "RUNPOD_NO", columnDefinition = "BINARY(16)", nullable = false)
    private UUID runpodNo;

    @PrePersist
    protected void generateUuid() {
        if (runpodNo == null) {
            runpodNo = UUID.randomUUID();
        }
    }

    @Column(name = "NAME", nullable = false, length = 255)
    private String name;

    @Column(name = "ADDRESS", nullable = false, length = 500)
    private String address;
}
