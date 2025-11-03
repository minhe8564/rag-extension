package com.ssafy.hebees.domain.chat.entity;

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

    @Field("FILE_NO")
    private UUID fileNo;

    @Field("NAME")
    private String name;

    @Field("TITLE")
    private String title;

    @Field("TYPE")
    private String type;

    @Field("INDEX")
    private Integer index;

    @Field("DOWNLOAD_URL")
    private String downloadUrl;

    @Field("SNIPPET")
    private String snippet;
}

