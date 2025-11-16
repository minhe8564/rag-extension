package com.ssafy.hebees.common.config;

import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.databind.DeserializationContext;
import com.fasterxml.jackson.databind.JsonDeserializer;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.databind.jsontype.BasicPolymorphicTypeValidator;
import com.fasterxml.jackson.databind.module.SimpleModule;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import java.io.IOException;
import java.time.Duration;
import java.util.Objects;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.boot.autoconfigure.data.redis.RedisProperties;
import org.springframework.cache.annotation.EnableCaching;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;
import org.springframework.data.redis.cache.RedisCacheConfiguration;
import org.springframework.data.redis.cache.RedisCacheManager;
import org.springframework.data.redis.connection.RedisPassword;
import org.springframework.data.redis.connection.RedisStandaloneConfiguration;
import org.springframework.data.redis.connection.lettuce.LettuceConnectionFactory;
import org.springframework.data.redis.serializer.Jackson2JsonRedisSerializer;
import org.springframework.data.redis.serializer.RedisSerializationContext.SerializationPair;
import org.springframework.data.redis.serializer.RedisSerializer;
import org.springframework.data.redis.serializer.StringRedisSerializer;
import org.springframework.util.StringUtils;

@EnableCaching
@Configuration
@RequiredArgsConstructor
public class CacheConfig {

    private static final int CACHE_DB_INDEX = 9;
    private static final Duration DEFAULT_TTL = Duration.ofHours(1);

    private final RedisProperties redisProperties;

    @Bean(name = "cacheLettuceConnectionFactory")
    public LettuceConnectionFactory cacheLettuceConnectionFactory() {
        RedisStandaloneConfiguration configuration = new RedisStandaloneConfiguration();
        configuration.setHostName(Objects.requireNonNull(redisProperties.getHost()));
        configuration.setPort(redisProperties.getPort());
        configuration.setDatabase(CACHE_DB_INDEX);

        if (StringUtils.hasText(redisProperties.getPassword())) {
            configuration.setPassword(RedisPassword.of(redisProperties.getPassword()));
        }
        if (StringUtils.hasText(redisProperties.getUsername())) {
            configuration.setUsername(redisProperties.getUsername());
        }

        LettuceConnectionFactory factory = new LettuceConnectionFactory(configuration);
        factory.afterPropertiesSet();
        factory.setValidateConnection(true);
        return factory;
    }

    @Bean
    @Primary
    public RedisCacheManager redisCacheManager(
        @Qualifier("cacheLettuceConnectionFactory") LettuceConnectionFactory connectionFactory
    ) {
        RedisCacheConfiguration configuration = RedisCacheConfiguration.defaultCacheConfig()
            .entryTtl(Objects.requireNonNull(DEFAULT_TTL))
            .serializeKeysWith(SerializationPair.fromSerializer(new StringRedisSerializer()))
            .serializeValuesWith(SerializationPair.fromSerializer(
                Objects.requireNonNull(createJacksonSerializer())));

        return RedisCacheManager.builder(Objects.requireNonNull(connectionFactory))
            .cacheDefaults(configuration)
            .transactionAware()
            .build();
    }

    private RedisSerializer<Object> createJacksonSerializer() {
        ObjectMapper mapper = new ObjectMapper();
        mapper.registerModule(new JavaTimeModule());
        mapper.disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);

        SimpleModule uuidModule = new SimpleModule();
        uuidModule.addSerializer(UUID.class,
            new com.fasterxml.jackson.databind.ser.std.ToStringSerializer());
        uuidModule.addDeserializer(UUID.class, new JsonDeserializer<UUID>() {
            @Override
            public UUID deserialize(JsonParser p, DeserializationContext ctxt) throws IOException {
                String text = p.getValueAsString();
                return text == null ? null : UUID.fromString(text);
            }
        });
        mapper.registerModule(uuidModule);

        mapper.activateDefaultTyping(
            BasicPolymorphicTypeValidator.builder()
                .allowIfBaseType(Object.class)
                .build(),
            ObjectMapper.DefaultTyping.EVERYTHING
        );

        return new Jackson2JsonRedisSerializer<>(mapper, Object.class);
    }

}
