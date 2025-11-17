package com.ssafy.hebees.notification.service;

import com.ssafy.hebees.common.exception.BusinessException;
import com.ssafy.hebees.common.exception.ErrorCode;
import com.ssafy.hebees.common.util.ValidationUtil;
import com.ssafy.hebees.notification.dto.request.NotificationCursorRequest;
import com.ssafy.hebees.notification.dto.response.NotificationCursorResponse;
import com.ssafy.hebees.notification.entity.Notification;
import com.ssafy.hebees.notification.repository.NotificationRepository;
import com.ssafy.hebees.user.entity.User;
import com.ssafy.hebees.user.repository.UserRepository;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class NotificationService {

    private final NotificationRepository notificationRepository;
    private final UserRepository userRepository;

    /**
     * ingest summary 완료 시점에 알림을 생성합니다. 중복 생성을 막기 위해 (USER_NO, EVENT_TYPE, REFERENCE_ID) 조합 기준으로 한
     * 번만 저장합니다.
     *
     * @param userNo         알림 대상 사용자 UUID (USER.USER_NO)
     * @param summaryEventId Redis summary 스트림 ID (REFERENCE_ID 로 사용)
     * @param total          총 작업 수
     * @param successCount   성공 수
     * @param failedCount    실패 수
     */
    @Transactional
    public void saveIngestSummaryNotification(
        UUID userNo,
        String summaryEventId,
        int total,
        int successCount,
        int failedCount
    ) {
        String eventType = "INGEST_SUMMARY_COMPLETED";
        String referenceId = summaryEventId;

        Optional<Notification> existing =
            notificationRepository.findByUser_UuidAndEventTypeAndReferenceIdAndDeletedAtIsNull(
                userNo,
                eventType,
                referenceId
            );

        if (existing.isPresent()) {
            // 동일 summary 이벤트에 대해서는 한 번만 저장
            return;
        }

        User userRef = userRepository.getReferenceById(userNo);
        String title = "문서 수집이 완료되었습니다.";

        Notification notification = Notification.builder()
            .user(userRef)
            .category("INGEST")
            .eventType(eventType)
            .referenceId(referenceId)
            .title(title)
            .total(total)
            .successCount(successCount)
            .failedCount(failedCount)
            .build();

        notificationRepository.save(notification);
    }

    /**
     * 현재 사용자의 알림을 커서 기반으로 조회합니다.
     *
     * @param userNo  사용자 ID
     * @param request 커서/limit 정보
     * @return 알림 커서 응답
     */
    @Transactional(readOnly = true)
    public NotificationCursorResponse listNotifications(UUID userNo,
        NotificationCursorRequest request) {
        UUID owner = ValidationUtil.require(userNo);

        NotificationCursorRequest effectiveRequest = request != null
            ? request
            : new NotificationCursorRequest(null, null);

        int requestedSize = effectiveRequest.limit();
        LocalDateTime cursor = effectiveRequest.cursor();

        int fetchSize = requestedSize + 1;
        Pageable pageable = PageRequest.of(0, fetchSize,
            Sort.by(Sort.Direction.DESC, "createdAt"));

        List<Notification> fetched = cursor == null
            ? notificationRepository.findByUser_UuidAndDeletedAtIsNullOrderByCreatedAtDesc(
            owner, pageable)
            : notificationRepository
                .findByUser_UuidAndDeletedAtIsNullAndCreatedAtBeforeOrderByCreatedAtDesc(
                    owner, cursor, pageable);

        boolean hasNext = fetched.size() > requestedSize;
        List<Notification> limited = hasNext
            ? new ArrayList<>(fetched.subList(0, requestedSize))
            : new ArrayList<>(fetched);

        LocalDateTime nextCursor = hasNext && !limited.isEmpty()
            ? limited.getLast().getCreatedAt()
            : null;

        // 최신순 정렬로 가져온 뒤, 클라이언트 편의를 위해 오래된 순으로 반환
        Collections.reverse(limited);

        List<NotificationCursorResponse.NotificationItemResponse> data = limited.stream()
            .map(n -> NotificationCursorResponse.NotificationItemResponse.builder()
                .notificationNo(n.getNotificationNo())
                .category(n.getCategory())
                .eventType(n.getEventType())
                .referenceId(n.getReferenceId())
                .title(n.getTitle())
                .total(n.getTotal())
                .successCount(n.getSuccessCount())
                .failedCount(n.getFailedCount())
                .isRead(n.isRead())
                .createdAt(n.getCreatedAt())
                .build())
            .toList();

        NotificationCursorResponse.Pagination pagination =
            new NotificationCursorResponse.Pagination(hasNext, nextCursor, data.size());

        return new NotificationCursorResponse(data, pagination);
    }

    /**
     * 알림을 읽음 처리합니다.
     *
     * @param userNo         현재 사용자 ID
     * @param notificationNo 알림 ID
     */
    @Transactional
    public void markAsRead(UUID userNo, UUID notificationNo) {
        UUID owner = ValidationUtil.require(userNo);
        UUID targetId = ValidationUtil.require(notificationNo);

        Notification notification = notificationRepository.findById(targetId)
            .orElseThrow(() -> new BusinessException(ErrorCode.NOT_FOUND));

        if (!owner.equals(notification.getUser().getUuid())) {
            throw new BusinessException(ErrorCode.OWNER_ACCESS_DENIED);
        }

        if (!notification.isRead()) {
            notification.markAsRead();
        }
    }

    /**
     * 알림을 삭제합니다.
     *
     * @param userNo         현재 사용자 ID
     * @param notificationNo 알림 ID
     */
    @Transactional
    public void delete(UUID userNo, UUID notificationNo) {
        UUID owner = ValidationUtil.require(userNo);
        UUID targetId = ValidationUtil.require(notificationNo);

        Notification notification = notificationRepository.findById(targetId)
            .orElseThrow(() -> new BusinessException(ErrorCode.NOT_FOUND));

        if (!owner.equals(notification.getUser().getUuid())) {
            throw new BusinessException(ErrorCode.OWNER_ACCESS_DENIED);
        }

        notificationRepository.delete(notification);
    }
}
