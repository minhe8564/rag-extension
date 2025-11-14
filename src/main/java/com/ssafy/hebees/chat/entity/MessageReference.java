package com.ssafy.hebees.chat.entity;

import java.util.UUID;
import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import org.springframework.data.mongodb.core.mapping.Field;

@Getter
@Builder
@AllArgsConstructor(access = AccessLevel.PRIVATE)
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class MessageReference {

    @Field("fileNo")
    private UUID fileNo;

    @Field("name")
    private String name;

    @Field("title")
    private String title;

    @Field("type")
    private String type;

    @Field("index")
    private Integer index;

    @Field("downloadUrl")
    private String downloadUrl;

    @Field("snippet")
    private String snippet;
}

