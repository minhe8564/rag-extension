package com.ssafy.hebees.chat.config;

import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Getter
@Setter
@Component
@ConfigurationProperties(prefix = "gemini")
public class GeminiProperties {

    private String baseUrl = "https://generativelanguage.googleapis.com";
    private String version = "v1beta";
    private String defaultModel = "gemini-2.5-flash";
    private Double defaultTemperature = 0.1d;
    private Integer defaultMaxOutputTokens = 1024;
    private String defaultApiKey;
}

