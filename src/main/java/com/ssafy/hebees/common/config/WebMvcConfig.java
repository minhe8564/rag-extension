package com.ssafy.hebees.common.config;

import com.ssafy.hebees.common.interceptor.ActiveUserTrackingInterceptor;
import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
@RequiredArgsConstructor
public class WebMvcConfig implements WebMvcConfigurer {

    private final ActiveUserTrackingInterceptor activeUserTrackingInterceptor;

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(activeUserTrackingInterceptor)
            .addPathPatterns("/**")
            .excludePathPatterns(
                "/actuator/**",
                "/swagger-ui/**",
                "/v3/api-docs/**",
                "/auth/health"
            );
    }
}
