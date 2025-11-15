package com.ssafy.hebees.common.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.auditing.DateTimeProvider;
import org.springframework.data.jpa.repository.config.EnableJpaAuditing;

import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.util.Optional;

/**
 * JPA Auditing 설정 클래스
 *
 * @CreatedDate, @LastModifiedDate에 자동으로 KST 시간을 저장하도록 설정
 */
@Configuration
@EnableJpaAuditing(dateTimeProviderRef = "kstDateTimeProvider")
public class JpaAuditingConfig {

    /**
     * JPA Auditing에서 사용할 KST 기반 시간 제공자
     *
     * @return KST 타임존의 현재 시간을 반환하는 DateTimeProvider
     */
    @Bean
    public DateTimeProvider kstDateTimeProvider() {
        return () -> Optional.of(
            ZonedDateTime.now(ZoneId.of("Asia/Seoul"))
                .toLocalDateTime()
        );
    }
}
