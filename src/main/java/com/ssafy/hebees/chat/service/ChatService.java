package com.ssafy.hebees.chat.service;

import com.ssafy.hebees.chat.dto.request.SessionCreateRequest;
import com.ssafy.hebees.chat.dto.request.SessionListRequest;
import com.ssafy.hebees.chat.dto.request.SessionUpdateRequest;
import com.ssafy.hebees.chat.dto.response.SessionCreateResponse;
import com.ssafy.hebees.chat.dto.response.SessionHistoryResponse;
import com.ssafy.hebees.chat.dto.response.SessionResponse;
import com.ssafy.hebees.common.dto.PageRequest;
import com.ssafy.hebees.common.dto.PageResponse;

import java.util.UUID;

public interface ChatService {

    PageResponse<SessionResponse> getSessions(UUID userNo, PageRequest pageRequest,
        SessionListRequest listRequest);

    PageResponse<SessionResponse> getAllSessions(PageRequest pageRequest,
        SessionListRequest listRequest);

    PageResponse<SessionHistoryResponse> getUserChatHistory(UUID userNo, PageRequest pageRequest,
        SessionListRequest listRequest);

    SessionResponse getSession(UUID userNo, UUID sessionNo);

    SessionCreateResponse createSession(UUID userNo, SessionCreateRequest request);

    void updateSession(UUID userNo, UUID sessionNo, SessionUpdateRequest request);

    void deleteSession(UUID userNo, UUID sessionNo);
}



