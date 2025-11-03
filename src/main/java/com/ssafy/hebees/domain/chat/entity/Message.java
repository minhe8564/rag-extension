package com.ssafy.hebees.domain.chat.entity;

//import java.time.LocalDateTime;
//import java.util.ArrayList;
//import java.util.List;
//import java.util.UUID;
//import lombok.AccessLevel;
//import lombok.AllArgsConstructor;
//import lombok.Builder;
//import lombok.Getter;
//import lombok.NoArgsConstructor;
//import org.bson.types.ObjectId;
//import org.springframework.data.annotation.CreatedDate;
//import org.springframework.data.annotation.Id;
//import org.springframework.data.mongodb.core.index.CompoundIndex;
//import org.springframework.data.mongodb.core.index.CompoundIndexes;
//import org.springframework.data.mongodb.core.index.Indexed;
//import org.springframework.data.mongodb.core.mapping.Document;
//import org.springframework.data.mongodb.core.mapping.Field;
//
//@Getter
//@Builder(toBuilder = true)
//@AllArgsConstructor(access = AccessLevel.PRIVATE)
//@NoArgsConstructor(access = AccessLevel.PROTECTED)
//@Document(collection = "MESSAGE")
//@CompoundIndexes({
//    // 세션별 최신 스크롤 조회에 유용
//    @CompoundIndex(name = "IDX_SESSION_TIMESTAMP_DESC", def = "{'SESSION_NO': 1, 'CREATED_AT': -1}"),
//    @CompoundIndex(name = "IDX_SESSION_SEQ_DESC", def = "{'SESSION_NO': 1, 'SEQ': -1}")
//})
//public class Message {
//
//    @Id
//    private ObjectId id; // _id
//
//    @Field("SESSION_NO")
//    private UUID sessionNo; // 세션 ID
//
//    @Indexed(name = "UK_MESSAGE_NO", unique = true)
//    @Field("MESSAGE_NO")
//    private UUID messageNo; // 메시지 ID
//
//    @Field("ROLE")
//    private MessageRole role; // 메시지 역할
//
//    @Field("CONTENT")
//    private String content; // 내용
//
//    @CreatedDate
//    @Field("CREATED_AT")
//    private LocalDateTime createdAt; // 생성 시각
//
//    @Field("SEQ")
//    private Long seq; // 커서 페이지용
//
//    @Field("USER_NO")
//    private UUID userNo; // 사용자 ID
//
//    @Field("LLM_NO")
//    private UUID llmNo; // LLM ID
//
//    @Field("INPUT_TOKENS")
//    private Long inputTokens; // 입력 토큰 사용량
//
//    @Field("OUTPUT_TOKENS")
//    private Long outputTokens; // 출력 토큰 사용량
//
//    @Field("TOTAL_TOKENS")
//    private Long totalTokens; // 총 토큰 사용량
//
//    @Field("RESPONSE_TIME_MS")
//    private Long responseTimeMs; // 응답 시간
//
//    @Builder.Default
//    @Field("REFERENCES")
//    private List<MessageReference> referencedDocuments = new ArrayList<>();
//}

