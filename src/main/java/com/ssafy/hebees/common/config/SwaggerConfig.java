package com.ssafy.hebees.common.config;

import io.swagger.v3.oas.models.Components;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.security.SecurityRequirement;
import io.swagger.v3.oas.models.security.SecurityScheme;
import io.swagger.v3.oas.models.servers.Server;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.beans.factory.annotation.Value;

@Configuration
public class SwaggerConfig {

    @Value("${spring.mvc.servlet.path:/}")
    private String servletPath;

    @Bean
    public OpenAPI openAPI() {
        String url = normalize(servletPath);

        Info info = new Info()
            .title("HEBEES API")
            .description("HEBEES Spring Boot API 문서")
            .version("v1.0.0");

        // JWT 인증 스키마 설정
        String securitySchemeName = "bearerAuth";
        SecurityScheme securityScheme = new SecurityScheme()
            .name(securitySchemeName)
            .type(SecurityScheme.Type.HTTP)
            .scheme("bearer")
            .bearerFormat("JWT")
            .description("JWT 토큰을 입력하세요. 예: Bearer your-jwt-token");

        // 보안 요구사항 설정
        SecurityRequirement securityRequirement = new SecurityRequirement().addList(
            securitySchemeName);

        return new OpenAPI()
            .addServersItem(new Server().url(url))
            .info(info)
            .components(new Components().addSecuritySchemes(securitySchemeName, securityScheme))
            .addSecurityItem(securityRequirement);
    }

    private static String normalize(String p) {
        if (p == null || p.isBlank()) {
            return "/";
        }
        String s = p.startsWith("/") ? p : "/" + p;
        return (s.endsWith("/") && s.length() > 1) ? s.substring(0, s.length() - 1) : s;
    }
}
