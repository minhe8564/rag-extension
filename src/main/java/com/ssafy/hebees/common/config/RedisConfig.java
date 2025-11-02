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
}

