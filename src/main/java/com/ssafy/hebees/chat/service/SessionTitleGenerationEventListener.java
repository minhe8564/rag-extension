package com.ssafy.hebees.chat.service;

import com.ssafy.hebees.chat.event.SessionTitleGenerationEvent;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;
import org.springframework.transaction.event.TransactionPhase;
import org.springframework.transaction.event.TransactionalEventListener;

@Component
@RequiredArgsConstructor
public class SessionTitleGenerationEventListener {

    private final SessionTitleAsyncService sessionTitleAsyncService;

    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    public void handleSessionTitleGeneration(SessionTitleGenerationEvent event) {
        sessionTitleAsyncService.generateSessionTitle(event.sessionNo(), event.query());
    }
}

