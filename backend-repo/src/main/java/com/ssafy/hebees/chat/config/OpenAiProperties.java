package com.ssafy.hebees.chat.config;

import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Getter
@Setter
@Component
@ConfigurationProperties(prefix = "openai")
public class OpenAiProperties {

    private String baseUrl = "https://api.openai.com";
    private String chatPath = "/v1/chat/completions";
    private String defaultModel = "gpt-4o";
    private Double defaultTemperature = 0.1d;
    private Integer defaultMaxTokens = 1024;
    private String organization;
    private String defaultApiKey;
}

