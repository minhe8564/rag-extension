package com.ssafy.hebees.domain.chat.entity;

import com.ssafy.hebees.global.entity.BaseSoftDeleteEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.PrePersist;
import jakarta.persistence.Table;
import java.time.LocalDateTime;
import java.util.UUID;
import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.SQLDelete;

@Entity
@Table(name = "SESSION")
@Getter
@Builder(toBuilder = true)
@AllArgsConstructor(access = AccessLevel.PRIVATE)
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@SQLDelete(sql = "UPDATE SESSION SET DELETED_AT = CURRENT_TIMESTAMP WHERE SESSION_NO = ?")
public class Session extends BaseSoftDeleteEntity {

    @Id
    @Column(name = "SESSION_NO", columnDefinition = "BINARY(16)", nullable = false)
    private UUID sessionNo; // 세션 ID

    @PrePersist
    protected void generateUuid() {
        if (sessionNo == null) {
            sessionNo = UUID.randomUUID();
        }
    }

    @Column(name = "TITLE", nullable = false, length = 50)
    private String title; // 세션명

    @Column(name = "USER_NO", columnDefinition = "BINARY(16)", nullable = false, updatable = false)
    private UUID userNo; // 세션 소유자 ID

    @Column(name = "LLM_NO", columnDefinition = "BINARY(16)", nullable = false)
    private UUID llmNo; // 사용할 LLM ID

    @Column(name = "LAST_REQUESTED_AT", nullable = false)
    private LocalDateTime lastRequestedAt; // 마지막 질문 시작

    public void updateSettings(String title, UUID llmNo) {
        this.title = title;
        this.llmNo = llmNo;
    }

    public void updateLastRequestedAt(LocalDateTime lastRequestedAt) {
        this.lastRequestedAt = lastRequestedAt;
    }
}
