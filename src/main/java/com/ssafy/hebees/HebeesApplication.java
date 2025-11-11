package com.ssafy.hebees;

import jakarta.annotation.PostConstruct;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.annotation.EnableScheduling;

import java.util.TimeZone;

@SpringBootApplication
@EnableScheduling
@EnableAsync
public class HebeesApplication {

    /**
     * 애플리케이션 시작 시 JVM 기본 타임존을 KST로 설정
     * 모든 자바 시간 관련 API(LocalDateTime.now(), new Date() 등)가 KST를 기본으로 사용
     */
    @PostConstruct
    public void init() {
        TimeZone.setDefault(TimeZone.getTimeZone("Asia/Seoul"));
    }

    public static void main(String[] args) {
        SpringApplication.run(HebeesApplication.class, args);
    }

}
