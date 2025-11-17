package com.ssafy.hebees.notification.controller;

import com.ssafy.hebees.common.exception.BusinessException;
import com.ssafy.hebees.common.exception.ErrorCode;
import com.ssafy.hebees.common.response.BaseResponse;
import com.ssafy.hebees.common.util.SecurityUtil;
import com.ssafy.hebees.notification.dto.request.NotificationCursorRequest;
import com.ssafy.hebees.notification.dto.response.NotificationCursorResponse;
import com.ssafy.hebees.notification.service.NotificationService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/notifications")
@RequiredArgsConstructor
@Tag(name = "Notification", description = "알림 조회 API")
public class NotificationController {

    private final NotificationService notificationService;

    @GetMapping
    @Operation(summary = "알림 목록 조회", description = "현재 로그인한 사용자의 전체 알림을 커서 기반으로 조회합니다.")
    @ApiResponse(responseCode = "200", description = "알림 목록 조회 성공")
    public ResponseEntity<BaseResponse<NotificationCursorResponse>> listNotifications(
        @Valid @ModelAttribute NotificationCursorRequest cursorRequest
    ) {
        UUID userNo = SecurityUtil.getCurrentUserUuid()
            .orElseThrow(() -> new BusinessException(ErrorCode.INVALID_ACCESS_TOKEN));
        NotificationCursorResponse response = notificationService.listNotifications(userNo,
            cursorRequest);
        return ResponseEntity.ok(BaseResponse.success(response));
    }

    @PatchMapping("/{notificationNo}/read")
    @Operation(summary = "알림 읽음 처리", description = "지정한 알림을 읽음 상태로 변경합니다.")
    @ApiResponse(responseCode = "200", description = "알림 읽음 처리 성공")
    public ResponseEntity<BaseResponse<Void>> markNotificationAsRead(
        @PathVariable("notificationNo") UUID notificationNo
    ) {
        UUID userNo = SecurityUtil.getCurrentUserUuid()
            .orElseThrow(() -> new BusinessException(ErrorCode.INVALID_ACCESS_TOKEN));
        notificationService.markAsRead(userNo, notificationNo);
        return ResponseEntity.ok(BaseResponse.success(null));
    }

    @DeleteMapping("/{notificationNo}")
    @Operation(summary = "알림 삭제", description = "지정한 알림을 삭제합니다.")
    @ApiResponse(responseCode = "200", description = "알림 삭제 성공")
    public ResponseEntity<BaseResponse<Void>> deleteNotification(
        @PathVariable("notificationNo") UUID notificationNo
    ) {
        UUID userNo = SecurityUtil.getCurrentUserUuid()
            .orElseThrow(() -> new BusinessException(ErrorCode.INVALID_ACCESS_TOKEN));
        notificationService.delete(userNo, notificationNo);
        return ResponseEntity.ok(BaseResponse.success(null));
    }
}
