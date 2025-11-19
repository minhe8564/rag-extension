package com.ssafy.hebees.notification.repository;

import com.ssafy.hebees.notification.entity.Notification;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

public interface NotificationRepository extends JpaRepository<Notification, UUID> {

    Optional<Notification> findByUser_UuidAndEventTypeAndReferenceIdAndDeletedAtIsNull(
        UUID userNo,
        String eventType,
        String referenceId
    );

    List<Notification> findByUser_UuidAndDeletedAtIsNullOrderByCreatedAtDesc(
        UUID userNo,
        Pageable pageable
    );

    List<Notification> findByUser_UuidAndDeletedAtIsNullAndCreatedAtBeforeOrderByCreatedAtDesc(
        UUID userNo,
        LocalDateTime cursor,
        Pageable pageable
    );
}
