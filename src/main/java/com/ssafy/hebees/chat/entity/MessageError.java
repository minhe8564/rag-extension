package com.ssafy.hebees.chat.entity;

import com.ssafy.hebees.common.entity.BaseEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
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
@Table(name = "MESSAGE_ERROR")
@Getter
@Builder(toBuilder = true)
@AllArgsConstructor(access = AccessLevel.PRIVATE)
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class MessageError extends BaseEntity {

    @Id
    @Column(name = "MESSAGE_ERROR_NO", columnDefinition = "BINARY(16)", nullable = false)
    private UUID messageErrorNo;

    @Column(name = "SESSION_NO", columnDefinition = "BINARY(16)", nullable = false)
    private UUID sessionNo;

    @Column(name = "REQUEST_NO", columnDefinition = "BINARY(16)", nullable = false)
    private UUID requestNo;

    @Enumerated(EnumType.STRING)
    @Column(name = "TYPE", nullable = false, length = 20)
    private MessageErrorType type;

    @PrePersist
    protected void generateUuid() {
        if (messageErrorNo == null) {
            messageErrorNo = UUID.randomUUID();
        }
    }
}
