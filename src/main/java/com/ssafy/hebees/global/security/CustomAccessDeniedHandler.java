package com.ssafy.hebees.global.security;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.ssafy.hebees.global.exception.ErrorCode;
import com.ssafy.hebees.global.exception.ErrorResponse;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import lombok.RequiredArgsConstructor;
import org.springframework.http.MediaType;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.web.access.AccessDeniedHandler;
import org.springframework.stereotype.Component;

@Component
@RequiredArgsConstructor
public class CustomAccessDeniedHandler implements AccessDeniedHandler {

    private final ObjectMapper objectMapper;

    @Override
    public void handle(HttpServletRequest request, HttpServletResponse response,
        AccessDeniedException accessDeniedException) throws IOException {

        ErrorCode errorCode = ErrorCode.PERMISSION_DENIED;

        response.setStatus(errorCode.getStatus().value());
        response.setContentType(MediaType.APPLICATION_JSON_VALUE);
        response.setCharacterEncoding("UTF-8");

        ErrorResponse body = ErrorResponse.of(errorCode);

        String jsonResponse = objectMapper.writeValueAsString(body);
        response.getWriter().write(jsonResponse);
    }
}
