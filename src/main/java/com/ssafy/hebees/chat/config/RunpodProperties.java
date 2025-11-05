package com.ssafy.hebees.chat.config;

import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Getter
@Setter
@Component
@ConfigurationProperties(prefix = "runpod")
public class RunpodProperties {

    /**
     * Runpod에서 제공하는 Ollama 엔드포인트 기본 URL.
     */
    private String baseUrl;

    /**
     * 챗봇 응답에 사용할 모델명.
     */
    private String model;
}

