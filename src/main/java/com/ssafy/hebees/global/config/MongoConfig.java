package com.ssafy.hebees.global.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.data.mongodb.config.EnableMongoAuditing;

@Configuration
@EnableMongoAuditing(modifyOnCreate = false)
public class MongoConfig {
}
