package com.ssafy.hebees.notification.entity;

import com.ssafy.hebees.common.entity.BaseSoftDeleteEntity;
import com.ssafy.hebees.user.entity.User;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.PrePersist;
import jakarta.persistence.Table;
import java.util.UUID;
import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.SQLDelete;

@Entity
@Table(name = "NOTIFICATION")
@Getter
@Builder(toBuilder = true)
@AllArgsConstructor(access = AccessLevel.PRIVATE)
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@SQLDelete(
    sql = "UPDATE NOTIFICATION SET DELETED_AT = CURRENT_TIMESTAMP WHERE NOTIFICATION_NO = ?"
)
public class Notification extends BaseSoftDeleteEntity {

    @Id
    @Column(
        name = "NOTIFICATION_NO",
        columnDefinition = "BINARY(16)",
        nullable = false,
        updatable = false
    )
    private UUID notificationNo;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(
        name = "USER_NO",
        referencedColumnName = "USER_NO",
        nullable = false,
        columnDefinition = "BINARY(16)"
    )
    private User user;

    @Column(name = "CATEGORY", nullable = false, length = 50)
    private String category;

    @Column(name = "EVENT_TYPE", nullable = false, length = 100)
    private String eventType;

    @Column(name = "REFERENCE_ID", nullable = false, length = 50)
    private String referenceId;

    @Column(name = "TITLE", nullable = false, length = 255)
    private String title;

    @Column(name = "TOTAL", nullable = false)
    private int total;

    @Column(name = "SUCCESS_COUNT", nullable = false)
    private int successCount;

    @Column(name = "FAILED_COUNT", nullable = false)
    private int failedCount;

    @Column(name = "IS_READ", nullable = false)
    @Builder.Default
    private boolean isRead = false;

    @PrePersist
    protected void generateUuid() {
        if (notificationNo == null) {
            notificationNo = UUID.randomUUID();
        }
    }

    public void markAsRead() {
        this.isRead = true;
    }

    public void updateCounts(int total, int successCount, int failedCount) {
        this.total = total;
        this.successCount = successCount;
        this.failedCount = failedCount;
    }
}

