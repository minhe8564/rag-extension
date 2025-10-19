package com.ssafy.hebees.config;

import com.ssafy.hebees.common.filter.JwtAuthenticationGatewayFilterFactory;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.cloud.gateway.route.RouteLocator;
import org.springframework.cloud.gateway.route.builder.RouteLocatorBuilder;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Slf4j
@Configuration
public class GatewayConfig {

    @Value("${gateway.backend.uri}")
    private String backendUri;

    @Value("${gateway.backend.path}")
    private String backendPath;

    @Value("${gateway.backend.rewrite-enabled:false}")
    private boolean rewriteEnabled;

    @Value("${gateway.backend.rewrite-pattern:}")
    private String rewritePattern;

    @Value("${gateway.backend.rewrite-replacement:}")
    private String rewriteReplacement;

    @Bean
    public RouteLocator customRouteLocator(
        RouteLocatorBuilder builder,
        JwtAuthenticationGatewayFilterFactory jwtFilter) {

        log.info("=== Gateway Route Configuration ===");
        log.info("Backend URI: {}", backendUri);
        log.info("Backend Path: {}", backendPath);
        log.info("Rewrite Enabled: {}", rewriteEnabled);
        if (rewriteEnabled) {
            log.info("Rewrite Pattern: {}", rewritePattern);
            log.info("Rewrite Replacement: {}", rewriteReplacement);
        }
        log.info("===================================");

        return builder.routes()
            .route("backend-service", r -> {
                var route = r.path(backendPath);

                // 필터 적용
                var filters = route.filters(f -> {
                    var filterSpec = f.filter(jwtFilter.apply(
                        new JwtAuthenticationGatewayFilterFactory.Config()));

                    // rewrite 설정이 활성화된 경우에만 적용
                    if (rewriteEnabled && rewritePattern != null && !rewritePattern.isEmpty()) {
                        log.info("Applying rewritePath: {} -> {}", rewritePattern,
                            rewriteReplacement);
                        filterSpec = filterSpec.rewritePath(rewritePattern, rewriteReplacement);
                    } else {
                        log.info("RewritePath disabled - passing through original path");
                    }

                    return filterSpec;
                });

                return filters.uri(backendUri);
            })
            .build();
    }
}

