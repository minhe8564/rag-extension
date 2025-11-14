package com.ssafy.hebees.common.config;

import java.util.Objects;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.boot.autoconfigure.data.redis.RedisProperties;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;
import org.springframework.data.redis.connection.RedisPassword;
import org.springframework.data.redis.connection.RedisStandaloneConfiguration;
import org.springframework.data.redis.connection.lettuce.LettuceConnectionFactory;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.util.StringUtils;

@Slf4j
@Configuration
@EnableConfigurationProperties(RedisProperties.class)
public class RedisConfig {

    private static final int DB_AUTH = 0; // 로그인 인증 정보
    private static final int DB_INGEST = 1; // ingest 정보
    private static final int DB_MONITORING = 2; // 모니터링 정보
    private static final int DB_ACTIVE_USER = 3; // 활성 사용자 정보
    private static final int DB_METRICS = 4; // 메트릭 정보
    private static final int DB_LOGIN_HISTORY = 8; // 로그인 사용자 정보
    private static final int DB_CHATBOT_USAGE = 8; // 챗봇 사용량 정보

    @Bean(name = "authLettuceConnectionFactory")
    @Primary
    public LettuceConnectionFactory authLettuceConnectionFactory(RedisProperties props) {
        return createLettuceConnectionFactory(props, DB_AUTH);
    }

    @Bean(name = "ingestLettuceConnectionFactory")
    public LettuceConnectionFactory ingestLettuceConnectionFactory(RedisProperties props) {
        return createLettuceConnectionFactory(props, DB_INGEST);
    }

    @Bean(name = "monitoringLettuceConnectionFactory")
    public LettuceConnectionFactory monitoringLettuceConnectionFactory(RedisProperties props) {
        return createLettuceConnectionFactory(props, DB_MONITORING);
    }

    @Bean(name = "activeUserLettuceConnectionFactory")
    public LettuceConnectionFactory activeUserLettuceConnectionFactory(RedisProperties props) {
        return createLettuceConnectionFactory(props, DB_ACTIVE_USER);
    }

    @Bean(name = "loginHistoryLettuceConnectionFactory")
    public LettuceConnectionFactory loginHistoryLettuceConnectionFactory(RedisProperties props) {
        return createLettuceConnectionFactory(props, DB_LOGIN_HISTORY);
    }

    @Bean(name = "metricsLettuceConnectionFactory")
    public LettuceConnectionFactory metricsLettuceConnectionFactory(RedisProperties props) {
        return createLettuceConnectionFactory(props, DB_METRICS, true);
    }

    @Bean(name = "chatbotUsageLettuceConnectionFactory")
    public LettuceConnectionFactory chatbotUsageLettuceConnectionFactory(RedisProperties props) {
        return createLettuceConnectionFactory(props, DB_CHATBOT_USAGE, true);
    }

    @Bean(name = "authRedisTemplate")
    @Primary
    public StringRedisTemplate authRedisTemplate(
        @Qualifier("authLettuceConnectionFactory") LettuceConnectionFactory connectionFactory) {
        return createRedisTemplate(connectionFactory);
    }

    @Bean(name = "ingestRedisTemplate")
    public StringRedisTemplate ingestRedisTemplate(
        @Qualifier("ingestLettuceConnectionFactory") LettuceConnectionFactory connectionFactory) {
        return createRedisTemplate(connectionFactory);
    }

    @Bean(name = "monitoringRedisTemplate")
    public StringRedisTemplate monitoringRedisTemplate(
        @Qualifier("monitoringLettuceConnectionFactory") LettuceConnectionFactory connectionFactory) {
        return createRedisTemplate(connectionFactory);
    }

    @Bean(name = "activeUserRedisTemplate")
    public StringRedisTemplate activeUserRedisTemplate(
        @Qualifier("activeUserLettuceConnectionFactory") LettuceConnectionFactory connectionFactory) {
        return createRedisTemplate(connectionFactory);
    }

    @Bean(name = "loginHistoryRedisTemplate")
    public StringRedisTemplate loginHistoryRedisTemplate(
        @Qualifier("loginHistoryLettuceConnectionFactory") LettuceConnectionFactory connectionFactory) {
        return createRedisTemplate(connectionFactory);
    }

    @Bean(name = "metricsRedisTemplate")
    public StringRedisTemplate metricsRedisTemplate(
        @Qualifier("metricsLettuceConnectionFactory") LettuceConnectionFactory connectionFactory) {
        return createRedisTemplate(connectionFactory, true);
    }

    @Bean(name = "chatbotUsageRedisTemplate")
    public StringRedisTemplate chatbotUsageRedisTemplate(
        @Qualifier("chatbotUsageLettuceConnectionFactory") LettuceConnectionFactory connectionFactory) {
        return createRedisTemplate(connectionFactory, true);
    }

    private LettuceConnectionFactory createLettuceConnectionFactory(RedisProperties props,
        int database) {
        return createLettuceConnectionFactory(props, database, false);
    }

    private LettuceConnectionFactory createLettuceConnectionFactory(
        RedisProperties props,
        int database,
        boolean validateConnection
    ) {
        RedisStandaloneConfiguration configuration = new RedisStandaloneConfiguration();
        configuration.setHostName(Objects.requireNonNull(props.getHost()));
        configuration.setPort(props.getPort());
        if (StringUtils.hasText(props.getPassword())) {
            configuration.setPassword(RedisPassword.of(props.getPassword()));
        }
        if (StringUtils.hasText(props.getUsername())) {
            configuration.setUsername(props.getUsername());
        }
        configuration.setDatabase(database);

        LettuceConnectionFactory factory = new LettuceConnectionFactory(configuration);
        if (validateConnection) {
            factory.afterPropertiesSet();
            factory.setValidateConnection(true);
        }
        return factory;
    }

    private StringRedisTemplate createRedisTemplate(LettuceConnectionFactory connectionFactory) {
        return createRedisTemplate(connectionFactory, false);
    }

    private StringRedisTemplate createRedisTemplate(
        LettuceConnectionFactory connectionFactory,
        boolean initialize
    ) {
        StringRedisTemplate template =
            new StringRedisTemplate(Objects.requireNonNull(connectionFactory));
        if (initialize) {
            template.afterPropertiesSet();
        }
        return template;
    }
}
