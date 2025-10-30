package com.ssafy.hebees.common.config;

import lombok.Getter;
import lombok.Setter;

import java.util.Arrays;
import java.util.List;

@Getter
@Setter
public class CorsProperties {
    private List<String> allowedOrigins = List.of("http://localhost:5173");
    private List<String> allowedMethods = Arrays.asList("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS");
    private List<String> allowedHeaders = List.of("*");
    private boolean allowCredentials = true;
    private List<String> exposedHeaders = Arrays.asList("Authorization", "Content-Type");
}
