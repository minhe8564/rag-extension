package com.ssafy.hebees.common.config;

import org.springframework.boot.autoconfigure.data.redis.RedisProperties;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;
import org.springframework.data.redis.connection.RedisPassword;
import org.springframework.data.redis.connection.RedisStandaloneConfiguration;
import org.springframework.data.redis.connection.lettuce.LettuceConnectionFactory;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.beans.factory.annotation.Qualifier;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@Configuration
@EnableConfigurationProperties(RedisProperties.class)
public class RedisConfig {

    @Bean(name = "authLettuceConnectionFactory")
    @Primary
    public LettuceConnectionFactory authLettuceConnectionFactory(RedisProperties props) {
        RedisStandaloneConfiguration conf = new RedisStandaloneConfiguration();
        conf.setHostName(props.getHost());
        conf.setPort(props.getPort());
        if (props.getPassword() != null && !props.getPassword().isEmpty()) {
            conf.setPassword(RedisPassword.of(props.getPassword()));
        }
        if (props.getUsername() != null && !props.getUsername().isEmpty()) {
            conf.setUsername(props.getUsername());
        }
        conf.setDatabase(0); // 로그인 정보는 DB0
        return new LettuceConnectionFactory(conf);
    }

    @Bean(name = "ingestLettuceConnectionFactory")
    public LettuceConnectionFactory ingestLettuceConnectionFactory(RedisProperties props) {
        RedisStandaloneConfiguration conf = new RedisStandaloneConfiguration();
        conf.setHostName(props.getHost());
        conf.setPort(props.getPort());
        if (props.getPassword() != null && !props.getPassword().isEmpty()) {
            conf.setPassword(RedisPassword.of(props.getPassword()));
        }
        if (props.getUsername() != null && !props.getUsername().isEmpty()) {
            conf.setUsername(props.getUsername());
        }
        conf.setDatabase(1); // ingest 정보는 DB1
        return new LettuceConnectionFactory(conf);
    }

    @Bean(name = "authRedisTemplate")
    @Primary
    public StringRedisTemplate authRedisTemplate(
        @Qualifier("authLettuceConnectionFactory") LettuceConnectionFactory connectionFactory) {
        return new StringRedisTemplate(connectionFactory);
    }

    @Bean(name = "ingestRedisTemplate")
    public StringRedisTemplate ingestRedisTemplate(
        @Qualifier("ingestLettuceConnectionFactory") LettuceConnectionFactory connectionFactory) {
        return new StringRedisTemplate(connectionFactory);
    }

    @Bean(name = "monitoringLettuceConnectionFactory")
    public LettuceConnectionFactory monitoringLettuceConnectionFactory(RedisProperties props) {
        RedisStandaloneConfiguration conf = new RedisStandaloneConfiguration();
        conf.setHostName(props.getHost());
        conf.setPort(props.getPort());
        if (props.getPassword() != null && !props.getPassword().isEmpty()) {
            conf.setPassword(RedisPassword.of(props.getPassword()));
        }
        if (props.getUsername() != null && !props.getUsername().isEmpty()) {
            conf.setUsername(props.getUsername());
        }
        conf.setDatabase(2); // 모니터링 정보는 DB2
        return new LettuceConnectionFactory(conf);
    }

    @Bean(name = "monitoringRedisTemplate")
    public StringRedisTemplate monitoringRedisTemplate(
        @Qualifier("monitoringLettuceConnectionFactory") LettuceConnectionFactory connectionFactory) {
        return new StringRedisTemplate(connectionFactory);
    }

    @Bean(name = "activeUserLettuceConnectionFactory")
    public LettuceConnectionFactory activeUserLettuceConnectionFactory(RedisProperties props) {
        RedisStandaloneConfiguration conf = new RedisStandaloneConfiguration();
        conf.setHostName(props.getHost());
        conf.setPort(props.getPort());
        if (props.getPassword() != null && !props.getPassword().isEmpty()) {
            conf.setPassword(RedisPassword.of(props.getPassword()));
        }
        if (props.getUsername() != null && !props.getUsername().isEmpty()) {
            conf.setUsername(props.getUsername());
        }
        conf.setDatabase(3); // 활성 사용자 정보는 DB3
        return new LettuceConnectionFactory(conf);
    }

    @Bean(name = "activeUserRedisTemplate")
    public StringRedisTemplate activeUserRedisTemplate(
        @Qualifier("activeUserLettuceConnectionFactory") LettuceConnectionFactory connectionFactory) {
        return new StringRedisTemplate(connectionFactory);
    }

    @Bean(name = "loginHistoryLettuceConnectionFactory")
    public LettuceConnectionFactory loginHistoryLettuceConnectionFactory(RedisProperties props) {
        RedisStandaloneConfiguration conf = new RedisStandaloneConfiguration();
        conf.setHostName(props.getHost());
        conf.setPort(props.getPort());
        if (props.getPassword() != null && !props.getPassword().isEmpty()) {
            conf.setPassword(RedisPassword.of(props.getPassword()));
        }
        if (props.getUsername() != null && !props.getUsername().isEmpty()) {
            conf.setUsername(props.getUsername());
        }
        conf.setDatabase(8); // 로그인 사용자 정보는 DB8
        return new LettuceConnectionFactory(conf);
    }

    @Bean(name = "loginHistoryRedisTemplate")
    public StringRedisTemplate loginHistoryRedisTemplate(
        @Qualifier("loginHistoryLettuceConnectionFactory") LettuceConnectionFactory connectionFactory) {
        return new StringRedisTemplate(connectionFactory);
    }

    @Bean(name = "metricsLettuceConnectionFactory")
    public LettuceConnectionFactory metricsLettuceConnectionFactory(RedisProperties props) {
        RedisStandaloneConfiguration conf = new RedisStandaloneConfiguration();
        conf.setHostName(props.getHost());
        conf.setPort(props.getPort());
        if (props.getPassword() != null && !props.getPassword().isEmpty()) {
            conf.setPassword(RedisPassword.of(props.getPassword()));
        }
        if (props.getUsername() != null && !props.getUsername().isEmpty()) {
            conf.setUsername(props.getUsername());
        }
        conf.setDatabase(4); // 메트릭 정보는 DB4

        LettuceConnectionFactory factory = new LettuceConnectionFactory(conf);
        factory.afterPropertiesSet();
        factory.setValidateConnection(true);
        return factory;
    }

    @Bean(name = "metricsRedisTemplate")
    public StringRedisTemplate metricsRedisTemplate(
        @Qualifier("metricsLettuceConnectionFactory") LettuceConnectionFactory connectionFactory) {
        StringRedisTemplate template = new StringRedisTemplate(connectionFactory);
        template.afterPropertiesSet();
        return template;
    }
}
