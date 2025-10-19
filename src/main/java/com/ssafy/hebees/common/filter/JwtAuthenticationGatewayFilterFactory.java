package com.ssafy.hebees.common.filter;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.ssafy.hebees.common.exception.CustomJwtException;
import com.ssafy.hebees.common.exception.ErrorCode;
import com.ssafy.hebees.common.exception.ErrorResponse;
import com.ssafy.hebees.common.util.JwtUtil;
import io.jsonwebtoken.JwtException;
import org.springframework.cloud.gateway.filter.GatewayFilter;
import org.springframework.cloud.gateway.filter.factory.AbstractGatewayFilterFactory;
import org.springframework.core.io.buffer.DataBuffer;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.http.server.reactive.ServerHttpResponse;
import org.springframework.web.server.ServerWebExchange;
import org.springframework.stereotype.Component;
import reactor.core.publisher.Mono;

import java.nio.charset.StandardCharsets;

@Component
public class JwtAuthenticationGatewayFilterFactory extends
    AbstractGatewayFilterFactory<JwtAuthenticationGatewayFilterFactory.Config> {

    private final JwtUtil jwtUtil;
    private final ObjectMapper objectMapper;

    public JwtAuthenticationGatewayFilterFactory(JwtUtil jwtUtil, ObjectMapper objectMapper) {
        super(Config.class);
        this.jwtUtil = jwtUtil;
        this.objectMapper = objectMapper;
    }

    @Override
    public GatewayFilter apply(Config config) {
        return (exchange, chain) -> {
            ServerHttpRequest request = exchange.getRequest();
            String path = request.getPath().toString();

            // 인증이 필요하지 않은 경로는 통과
            if (isPublicPath(path)) {
                return chain.filter(exchange);
            }

            // JWT 토큰 검증을 Reactive 방식으로 처리
            return validateJwtToken(exchange, request)
                .flatMap(token -> {
                    // JWT 검증 완료 후 원본 토큰을 그대로 백엔드로 전달
                    ServerHttpRequest modifiedRequest = request.mutate()
                        .header("X-JWT-Token", token)
                        .build();

                    return chain.filter(exchange.mutate().request(modifiedRequest).build());
                })
                .onErrorResume(CustomJwtException.class, e -> handleJwtException(exchange, e));
        };
    }

    /**
     * JWT 토큰 검증을 Reactive 방식으로 처리
     */
    private Mono<String> validateJwtToken(ServerWebExchange exchange, ServerHttpRequest request) {
        return Mono.fromCallable(() -> {
            String authorizationHeader = request.getHeaders().getFirst(HttpHeaders.AUTHORIZATION);
            String accessToken = JwtUtil.extractAccessToken(authorizationHeader);

            if (accessToken == null) {
                throw new CustomJwtException(ErrorCode.INVALID_TOKEN);
            }

            try {
                jwtUtil.validateToken(accessToken);
                return accessToken;
            } catch (JwtException | IllegalArgumentException e) {
                throw new CustomJwtException(ErrorCode.INVALID_ACCESS_TOKEN, e);
            }
        });
    }

    private boolean isPublicPath(String path) {
        return path.startsWith("/v3/api-docs") ||
            path.startsWith("/swagger-ui") ||
            path.startsWith("/swagger-ui.html") ||
            path.startsWith("/api/user/signup") ||
            path.startsWith("/api/auth");
    }

    /**
     * JWT 예외를 Reactive 방식으로 처리
     */
    private Mono<Void> handleJwtException(ServerWebExchange exchange, CustomJwtException e) {
        ServerHttpResponse response = exchange.getResponse();
        ErrorCode errorCode = e.getErrorCode();

        response.setStatusCode(HttpStatus.valueOf(errorCode.getStatus()));
        response.getHeaders().setContentType(MediaType.APPLICATION_JSON);

        ErrorResponse errorResponse = ErrorResponse.of(errorCode);

        try {
            String jsonResponse = objectMapper.writeValueAsString(errorResponse);
            DataBuffer buffer = response.bufferFactory()
                .wrap(jsonResponse.getBytes(StandardCharsets.UTF_8));
            return response.writeWith(Mono.just(buffer));
        } catch (Exception ex) {
            return response.setComplete();
        }
    }

    public static class Config {
        // 필터 설정이 필요한 경우 여기에 추가
    }
}
