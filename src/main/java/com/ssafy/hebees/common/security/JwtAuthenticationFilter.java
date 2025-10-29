package com.ssafy.hebees.common.security;

import com.ssafy.hebees.common.util.JwtUtil;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.web.authentication.WebAuthenticationDetailsSource;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.List;
import java.util.UUID;

@Slf4j
@Component
@RequiredArgsConstructor
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    private final JwtUtil jwtUtil;

    @Override
    protected void doFilterInternal(
        HttpServletRequest request,
        HttpServletResponse response,
        FilterChain filterChain
    ) throws ServletException, IOException {

        try {
            // Gateway에서 전달한 JWT 토큰 추출
            String jwtToken = request.getHeader("X-JWT-Token");

            if (jwtToken == null) {
                // Gateway를 거치지 않은 직접 요청의 경우 Authorization 헤더 확인
                jwtToken = JwtUtil.extractAccessToken(request);
            }

            if (jwtToken != null) {
                // 토큰에서 사용자 정보 추출
                String userUuidStr = jwtUtil.getSubject(jwtToken);
                String roleStr = jwtUtil.getRole(jwtToken);

                UUID userUuid = UUID.fromString(userUuidStr);
                String roleName = roleStr;

                log.debug("JWT 인증 성공: userUuid={}, role={}", userUuid, roleName);

                // Spring Security 인증 객체 생성
                List<SimpleGrantedAuthority> authorities = List.of(
                    new SimpleGrantedAuthority("ROLE_" + roleName)
                );

                UsernamePasswordAuthenticationToken authentication =
                    new UsernamePasswordAuthenticationToken(userUuid, null, authorities);

                authentication.setDetails(
                    new WebAuthenticationDetailsSource().buildDetails(request));

                // SecurityContext에 인증 정보 설정
                SecurityContextHolder.getContext().setAuthentication(authentication);
            }
        } catch (Exception e) {
            log.warn("JWT 인증 처리 중 오류 발생: {}", e.getMessage());
            // 오류가 발생해도 필터 체인은 계속 진행 (SecurityConfig에서 인증 체크)
        }

        filterChain.doFilter(request, response);
    }
}
