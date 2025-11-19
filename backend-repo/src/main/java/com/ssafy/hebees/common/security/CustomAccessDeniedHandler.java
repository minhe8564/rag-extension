package com.ssafy.hebees.common.security;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.ssafy.hebees.common.exception.ErrorCode;
import com.ssafy.hebees.common.exception.ErrorResponse;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.MediaType;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.web.access.AccessDeniedHandler;
import org.springframework.stereotype.Component;

@Slf4j
@Component
@RequiredArgsConstructor
public class CustomAccessDeniedHandler implements AccessDeniedHandler {

    private final ObjectMapper objectMapper;

    @Override
    public void handle(HttpServletRequest request, HttpServletResponse response,
        AccessDeniedException accessDeniedException) throws IOException {

        // SSE 스트리밍 요청이거나 응답이 이미 커밋된 경우 무시
        String acceptHeader = request.getHeader("Accept");
        boolean isSseRequest = acceptHeader != null && acceptHeader.contains("text/event-stream");
        boolean isResponseCommitted = response.isCommitted();

        if (isSseRequest || isResponseCommitted) {
            // SSE 스트리밍 중이거나 응답이 이미 커밋된 경우 로그를 남기지 않고 조용히 처리
            return;
        }

        ErrorCode errorCode = ErrorCode.PERMISSION_DENIED;

        try {
            response.setStatus(errorCode.getStatus().value());
            response.setContentType(MediaType.APPLICATION_JSON_VALUE);
            response.setCharacterEncoding("UTF-8");

            ErrorResponse body = ErrorResponse.of(errorCode);

            String jsonResponse = objectMapper.writeValueAsString(body);
            response.getWriter().write(jsonResponse);
        } catch (IllegalStateException e) {
            // 응답이 이미 커밋된 경우 무시
            log.debug("Response already committed, ignoring access denied: {}", e.getMessage());
        }
    }
}
