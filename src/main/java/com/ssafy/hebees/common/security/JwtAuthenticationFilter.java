package com.ssafy.hebees.common.security;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.ssafy.hebees.common.exception.ErrorCode;
import com.ssafy.hebees.common.exception.ErrorResponse;
import com.ssafy.hebees.common.util.JwtUtil;
import com.ssafy.hebees.user.entity.UserRole;
import io.jsonwebtoken.JwtException;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.http.MediaType;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.AuthorityUtils;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

@Component
@RequiredArgsConstructor
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    private final JwtUtil jwtUtil;
    private final ObjectMapper objectMapper;

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response,
        FilterChain filterChain)
        throws ServletException, IOException {

        String accessToken = JwtUtil.extractAccessToken(request);

        if (accessToken != null) {
            try {
                jwtUtil.validateToken(accessToken);

                String userUuid = jwtUtil.getSubject(accessToken);
                String roleClaim = jwtUtil.getRole(accessToken);

                List<GrantedAuthority> authorities;
                if (roleClaim == null || roleClaim.isBlank()) {
                    authorities = AuthorityUtils.NO_AUTHORITIES;
                } else {
                    try {
                        UserRole userRole = UserRole.valueOf(roleClaim);
                        authorities = AuthorityUtils.createAuthorityList("ROLE_" + userRole.name());
                    } catch (IllegalArgumentException e) {
                        setErrorResponse(response, ErrorCode.INVALID_ACCESS_TOKEN);
                        return;
                    }
                }

                Authentication authentication =
                    new UsernamePasswordAuthenticationToken(userUuid, null, authorities);
                SecurityContextHolder.getContext().setAuthentication(authentication);
            } catch (JwtException | IllegalArgumentException e) {
                setErrorResponse(response, ErrorCode.INVALID_ACCESS_TOKEN);
                return;
            }
        }

        filterChain.doFilter(request, response);
    }

    private void setErrorResponse(HttpServletResponse response, ErrorCode errorCode)
        throws IOException {
        response.setStatus(errorCode.getStatus().value());
        response.setContentType(MediaType.APPLICATION_JSON_VALUE);
        response.setCharacterEncoding("UTF-8");

        ErrorResponse body = ErrorResponse.of(errorCode);
        String jsonResponse = objectMapper.writeValueAsString(body);

        response.getWriter().write(jsonResponse);
    }

}
