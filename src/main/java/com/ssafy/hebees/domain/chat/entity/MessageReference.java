package com.ssafy.hebees.domain.chat.entity;

import java.util.UUID;
import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@Builder
@AllArgsConstructor(access = AccessLevel.PRIVATE)
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class MessageReference {

    private UUID fileNo;

    private String name;

    private String title;

    private String type;

    private Integer index;

    private String downloadUrl;

    private String snippet;
}

