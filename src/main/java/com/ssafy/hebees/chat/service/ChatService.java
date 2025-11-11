package com.ssafy.hebees.chat.service;

import com.ssafy.hebees.chat.dto.request.SessionCreateRequest;
import com.ssafy.hebees.chat.dto.request.SessionSearchRequest;
import com.ssafy.hebees.chat.dto.request.SessionUpdateRequest;
import com.ssafy.hebees.chat.dto.response.SessionCreateResponse;
import com.ssafy.hebees.chat.dto.response.SessionResponse;
import com.ssafy.hebees.common.dto.ListResponse;
import com.ssafy.hebees.common.dto.PageRequest;
import com.ssafy.hebees.common.dto.PageResponse;
import java.util.UUID;

public interface ChatService {

    ListResponse<SessionResponse> getSessions(UUID userNo, SessionSearchRequest listRequest);

    PageResponse<SessionResponse> getAllSessions(PageRequest pageRequest,
        SessionSearchRequest searchRequest);

    SessionResponse getSession(UUID userNo, UUID sessionNo);

    SessionCreateResponse createSession(UUID userNo, SessionCreateRequest request);

    void updateSession(UUID userNo, UUID sessionNo, SessionUpdateRequest request);

    void deleteSession(UUID userNo, UUID sessionNo);
}



