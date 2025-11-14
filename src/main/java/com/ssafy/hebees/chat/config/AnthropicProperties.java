package com.ssafy.hebees.chat.config;

import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Getter
@Setter
@Component
@ConfigurationProperties(prefix = "anthropic")
public class AnthropicProperties {

    private String baseUrl = "https://api.anthropic.com";
    private String messagesPath = "/v1/messages";
    private String defaultModel = "claude-sonnet-4-20250514";
    private Double defaultTemperature = 0.1d;
    private Integer defaultMaxTokens = 1024;
    private String apiVersion = "2023-06-01";
    private String defaultApiKey;
}

