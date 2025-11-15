package com.ssafy.hebees.chat.event;

import com.ssafy.hebees.chat.entity.MessageErrorType;
import com.ssafy.hebees.dashboard.service.DashboardMetricStreamService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.transaction.event.TransactionPhase;
import org.springframework.transaction.event.TransactionalEventListener;

@Slf4j
@Component
@RequiredArgsConstructor
public class MessageErrorEventListener {

    private final DashboardMetricStreamService dashboardMetricStreamService;

    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    public void handleMessageErrorCreated(MessageErrorCreatedEvent event) {
        if (event == null || event.type() == null) {
            log.warn("메시지 에러 이벤트 처리 실패 - 이벤트 또는 타입이 null 입니다.");
            return;
        }

        MessageErrorType type = event.type();
        long systemDelta = type == MessageErrorType.SYSTEM ? 1L : 0L;
        long responseDelta = type == MessageErrorType.RESPONSE ? 1L : 0L;

        if (systemDelta == 0L && responseDelta == 0L) {
            return;
        }

        try {
            dashboardMetricStreamService.incrementCurrentErrors(systemDelta, responseDelta);
        } catch (Exception e) {
            log.warn("에러 집계 업데이트 실패: type={}, systemDelta={}, responseDelta={}, reason={}",
                type, systemDelta, responseDelta, e.getMessage(), e);
        }
    }
}

