package com.ssafy.hebees.chat.config;

import com.ssafy.hebees.monitoring.entity.Runpod;
import com.ssafy.hebees.monitoring.repository.RunpodRepository;
import jakarta.annotation.PostConstruct;
import lombok.Getter;
import lombok.Setter;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;

@Slf4j
@Getter
@Setter
@Component
@ConfigurationProperties(prefix = "runpod")
public class RunpodProperties {

    /**
     * Runpod에서 제공하는 Ollama 엔드포인트 기본 URL. DB에서 조회한 주소로 설정됨
     */
    private String baseUrl;

    /**
     * 챗봇 응답에 사용할 모델명.
     */
    private String model;

    /**
     * DB에서 조회할 Runpod 이름 반드시 DB에 존재해야 함
     */
    @Value("${runpod.name:}")
    private String runpodName;

    /**
     * Runpod 공식 API 키 (모니터링용) Runpod 웹 콘솔에서 발급받은 API 키
     */
    @Value("${runpod.api-key:}")
    private String apiKey;

    /**
     * Runpod 공식 API 베이스 URL
     */
    @Value("${runpod.api-base-url:https://api.runpod.io/graphql}")
    private String apiBaseUrl;

    @Autowired(required = false)
    private RunpodRepository runpodRepository;

    /**
     * 애플리케이션 시작 시 DB에서 RunPod 정보 조회 DB에 반드시 데이터가 있어야 함
     */
    @PostConstruct
    public void initFromDatabase() {
        if (StringUtils.hasText(runpodName) && runpodRepository != null) {
            Runpod runpod = runpodRepository.findByName(runpodName)
                .orElseThrow(() -> new IllegalStateException(
                    String.format("DB에서 Runpod를 찾을 수 없습니다. name=%s", runpodName)));

            if (StringUtils.hasText(runpod.getAddress())) {
                this.baseUrl = runpod.getAddress();
                log.info("Runpod 정보를 DB에서 조회했습니다: name={}, address={}",
                    runpod.getName(), runpod.getAddress());
            } else {
                throw new IllegalStateException(
                    String.format("Runpod의 주소가 비어있습니다. name=%s", runpodName));
            }
        } else {
            if (!StringUtils.hasText(runpodName)) {
                log.warn("runpod.name이 설정되지 않았습니다. application.yml의 base-url을 사용합니다.");
            }
            if (runpodRepository == null) {
                log.warn("RunpodRepository가 주입되지 않았습니다. application.yml의 base-url을 사용합니다.");
            }
        }
    }
}
