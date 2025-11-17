package com.ssafy.hebees.chat.controller;

import com.ssafy.hebees.chat.dto.request.AskRequest;
import com.ssafy.hebees.chat.dto.request.MessageCreateRequest;
import com.ssafy.hebees.chat.dto.request.MessageCursorRequest;
import com.ssafy.hebees.chat.dto.request.SessionCreateRequest;
import com.ssafy.hebees.chat.dto.request.SessionSearchRequest;
import com.ssafy.hebees.chat.dto.request.SessionUpdateRequest;
import com.ssafy.hebees.chat.dto.response.AskResponse;
import com.ssafy.hebees.chat.dto.response.MessageCursorResponse;
import com.ssafy.hebees.chat.dto.response.MessageResponse;
import com.ssafy.hebees.chat.dto.response.ReferencedDocumentListResponse;
import com.ssafy.hebees.chat.dto.response.ReferencedDocumentResponse;
import com.ssafy.hebees.chat.dto.response.SessionCreateResponse;
import com.ssafy.hebees.chat.dto.response.SessionResponse;
import com.ssafy.hebees.chat.service.ChatAskService;
import com.ssafy.hebees.chat.service.ChatAskStreamService;
import com.ssafy.hebees.chat.service.ChatService;
import com.ssafy.hebees.chat.service.MessageService;
import com.ssafy.hebees.common.dto.ListResponse;
import com.ssafy.hebees.common.dto.PageRequest;
import com.ssafy.hebees.common.dto.PageResponse;
import com.ssafy.hebees.common.exception.BusinessException;
import com.ssafy.hebees.common.exception.ErrorCode;
import com.ssafy.hebees.common.response.BaseResponse;
import com.ssafy.hebees.common.util.SecurityUtil;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import java.net.URI;
import java.util.Objects;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;


@RestController
@RequestMapping("/chat")
@RequiredArgsConstructor
@Slf4j
@Tag(name = "채팅 관리", description = "채팅 관련 API")
public class ChatController {

    private final ChatService chatService;
    private final MessageService chatMessageService;
    private final ChatAskService chatAskService;
    private final ChatAskStreamService chatAskStreamService;

    @GetMapping("/sessions")
    @Operation(summary = "세션 목록 조회", description = "세션 목록을 조회합니다.")
    @ApiResponse(responseCode = "200", description = "세션 목록 조회 성공")
    public ResponseEntity<BaseResponse<ListResponse<SessionResponse>>> listSessions(
        @Valid @ModelAttribute SessionSearchRequest request
    ) {
        UUID userNo = SecurityUtil.getCurrentUserUuid()
            .orElseThrow(() -> new BusinessException(ErrorCode.INVALID_ACCESS_TOKEN));

        ListResponse<SessionResponse> sessions = chatService.getSessions(userNo, request);

        return ResponseEntity.ok(BaseResponse.of(HttpStatus.OK, sessions, "세션 목록 조회에 성공하였습니다."));
    }

    @GetMapping("/sessions/all")
    @Operation(summary = "[관리자] 전체 세션 목록 조회", description = "모든 사용자 세션 목록을 조회합니다.")
    @ApiResponse(responseCode = "200", description = "전체 세션 목록 조회 성공")
    public ResponseEntity<BaseResponse<PageResponse<SessionResponse>>> listAllSessions(
        @Valid @ModelAttribute PageRequest pageRequest,
        @Valid @ModelAttribute SessionSearchRequest searchRequest
    ) {
        String userRole = SecurityUtil.getCurrentUserRole()
            .orElseThrow(() -> new BusinessException(ErrorCode.INVALID_ACCESS_TOKEN));
        if (!Objects.equals(userRole, "ADMIN")) {
            throw new BusinessException(ErrorCode.PERMISSION_DENIED);
        }

        PageResponse<SessionResponse> sessions = chatService.getAllSessions(pageRequest,
            searchRequest);

        return ResponseEntity.ok(BaseResponse.of(HttpStatus.OK, sessions, "세션 목록 전체 조회에 성공하였습니다."));
    }

    @GetMapping("/sessions/{sessionNo}")
    @Operation(summary = "세션 조회", description = "세션을 조회합니다.")
    @ApiResponse(responseCode = "200", description = "세션 조회 성공")
    public ResponseEntity<BaseResponse<SessionResponse>> getSession(@PathVariable UUID sessionNo) {
        UUID userNo = SecurityUtil.getCurrentUserUuid()
            .orElseThrow(() -> new BusinessException(ErrorCode.INVALID_ACCESS_TOKEN));
        SessionResponse session = chatService.getSession(userNo, sessionNo);

        return ResponseEntity.ok(BaseResponse.of(HttpStatus.OK, session, "세션 조회에 성공하였습니다."));
    }

    @PostMapping("/sessions")
    @Operation(summary = "세션 생성", description = "새로운 세션을 생성합니다.")
    @ApiResponse(responseCode = "201", description = "세션 생성 성공")
    public ResponseEntity<BaseResponse<SessionCreateResponse>> createSession(
        @Valid @RequestBody SessionCreateRequest request) {
        UUID userNo = SecurityUtil.getCurrentUserUuid()
            .orElseThrow(() -> new BusinessException(ErrorCode.INVALID_ACCESS_TOKEN));
        SessionCreateResponse session = chatService.createSession(userNo, request);

        UUID sessionNo = session.sessionNo();
        String title = session.title();
        URI location = URI.create("/sessions/" + sessionNo);
        return ResponseEntity.created(location).body(
            BaseResponse.of(HttpStatus.CREATED,
                new SessionCreateResponse(sessionNo, title),
                "세션 생성에 성공하였습니다."));
    }


    @PutMapping("/sessions/{sessionNo}")
    @Operation(summary = "세션 수정", description = "세션 정보를 수정합니다.")
    @ApiResponse(responseCode = "200", description = "세션 정보 수정 성공")
    public ResponseEntity<BaseResponse<Void>> updateSession(@PathVariable UUID sessionNo,
        @Valid @RequestBody SessionUpdateRequest request) {
        UUID userNo = SecurityUtil.getCurrentUserUuid()
            .orElseThrow(() -> new BusinessException(ErrorCode.INVALID_ACCESS_TOKEN));
        chatService.updateSession(userNo, sessionNo, request);

        return ResponseEntity.ok(BaseResponse.of(HttpStatus.OK, null, "세션 수정에 성공하였습니다."));
    }

    @DeleteMapping("/sessions/{sessionNo}")
    @Operation(summary = "세션 삭제", description = "세션을 삭제합니다.")
    @ApiResponse(responseCode = "204", description = "세션 삭제 성공")
    public ResponseEntity<Void> deleteSession(@PathVariable UUID sessionNo) {
        UUID userNo = SecurityUtil.getCurrentUserUuid()
            .orElseThrow(() -> new BusinessException(ErrorCode.INVALID_ACCESS_TOKEN));
        chatService.deleteSession(userNo, sessionNo);

        return ResponseEntity.noContent().build();
    }

    @GetMapping("/sessions/{sessionNo}/messages")
    @Operation(summary = "메시지 목록 조회", description = "메시지 목록을 조회합니다.")
    @ApiResponse(responseCode = "200", description = "메시지 목록 조회 성공")
    public ResponseEntity<BaseResponse<MessageCursorResponse>> listSessionMessages(
        @PathVariable UUID sessionNo,
        @Valid @ModelAttribute MessageCursorRequest cursorRequest) {
        UUID userNo = SecurityUtil.getCurrentUserUuid()
            .orElseThrow(() -> new BusinessException(ErrorCode.INVALID_ACCESS_TOKEN));
        MessageCursorResponse messages = chatMessageService.listMessages(userNo, sessionNo,
            cursorRequest);
        return ResponseEntity.ok(BaseResponse.of(HttpStatus.OK, messages, "메시지 목록 조회 성공"));
    }

    @GetMapping("/sessions/{sessionNo}/messages/{messageNo}")
    @Operation(summary = "메시지 조회", description = "메시지를 조회합니다.")
    @ApiResponse(responseCode = "200", description = "메시지 조회 성공")
    public ResponseEntity<BaseResponse<MessageResponse>> getMessage(
        @PathVariable UUID sessionNo, @PathVariable UUID messageNo) {
        UUID userNo = SecurityUtil.getCurrentUserUuid()
            .orElseThrow(() -> new BusinessException(ErrorCode.INVALID_ACCESS_TOKEN));
        MessageResponse message = chatMessageService.getMessage(userNo, sessionNo, messageNo);
        return ResponseEntity.ok(BaseResponse.of(HttpStatus.OK, message, "메시지 조회 성공"));
    }

    @GetMapping("/sessions/{sessionNo}/messages/{messageNo}/documents")
    @Operation(summary = "참조 문서 목록 조회", description = "참조된 문서의 목록을 조회합니다.")
    @ApiResponse(responseCode = "200", description = "참조 문서 목록 조회 성공.")
    public ResponseEntity<BaseResponse<ReferencedDocumentListResponse>> listReferencedDocuments(
        @PathVariable UUID sessionNo, @PathVariable UUID messageNo) {
        UUID userNo = SecurityUtil.getCurrentUserUuid()
            .orElseThrow(() -> new BusinessException(ErrorCode.INVALID_ACCESS_TOKEN));

        ReferencedDocumentListResponse documents = chatMessageService.listReferencedDocuments(
            userNo, sessionNo, messageNo);
        return ResponseEntity.ok(BaseResponse.of(HttpStatus.OK, documents, "참조 문서 목록 조회 성공"));
    }

    @GetMapping("/sessions/{sessionNo}/messages/{messageNo}/documents/{documentNo}")
    @Operation(summary = "참조 문서 조회", description = "참조된 문서를 조회합니다.")
    @ApiResponse(responseCode = "200", description = "참조 문서 조회 성공.")
    public ResponseEntity<BaseResponse<ReferencedDocumentResponse>> getReferencedDocument(
        @PathVariable UUID sessionNo, @PathVariable UUID messageNo, @PathVariable UUID documentNo) {
        UUID userNo = SecurityUtil.getCurrentUserUuid()
            .orElseThrow(() -> new BusinessException(ErrorCode.INVALID_ACCESS_TOKEN));
        ReferencedDocumentResponse document = chatMessageService.getReferencedDocument(userNo,
            sessionNo, messageNo, documentNo);
        return ResponseEntity.ok(BaseResponse.of(HttpStatus.OK, document, "참조 문서 조회 성공"));
    }

    @PostMapping("/sessions/{sessionNo}/ask")
    @Operation(summary = "일반 LLM 챗봇에게 질문하기", description = "일반 LLM 챗봇에게 질문을 합니다.")
    @ApiResponse(responseCode = "200", description = "일반 LLM 챗봇에게 질문을 성공하였습니다.")
    public ResponseEntity<BaseResponse<AskResponse>> ask(
        @PathVariable UUID sessionNo,
        @Valid @RequestBody AskRequest request
    ) {
        UUID userNo = SecurityUtil.getCurrentUserUuid()
            .orElseThrow(() -> new BusinessException(ErrorCode.INVALID_ACCESS_TOKEN));

        AskResponse response = chatAskService.ask(userNo, sessionNo, request);

        return ResponseEntity.ok(
            BaseResponse.of(
                HttpStatus.OK,
                response,
                "일반 LLM 챗봇에게 질문을 성공하였습니다."
            ));
    }

    @PostMapping("/ask")
    @Operation(summary = "일반 LLM 챗봇에게 질문하기", description = "일반 LLM 챗봇에게 질문을 합니다.")
    @ApiResponse(responseCode = "200", description = "일반 LLM 챗봇에게 질문을 성공하였습니다.")
    public ResponseEntity<BaseResponse<AskResponse>> ask(
        @Valid @RequestBody AskRequest request
    ) {
        UUID userNo = SecurityUtil.getCurrentUserUuid()
            .orElseThrow(() -> new BusinessException(ErrorCode.INVALID_ACCESS_TOKEN));

        AskResponse response = chatAskService.ask(userNo, request.sessionNo(), request);

        return ResponseEntity.ok(
            BaseResponse.of(
                HttpStatus.OK,
                response,
                "일반 LLM 챗봇에게 질문을 성공하였습니다."
            ));
    }

    @PostMapping(value = "/sessions/{sessionNo}/ask/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    @Operation(summary = "세션 LLM 챗봇에게 질문하기(SSE)", description = "세션 지정 일반 LLM 챗봇에게 질문을 하고 스트리밍으로 응답을 수신합니다.")
    public SseEmitter askStream(
        @PathVariable UUID sessionNo,
        @Valid @RequestBody AskRequest request
    ) {
        UUID userNo = SecurityUtil.getCurrentUserUuid()
            .orElseThrow(() -> new BusinessException(ErrorCode.INVALID_ACCESS_TOKEN));
        return chatAskStreamService.askStream(userNo, sessionNo, request);
    }

    @PostMapping(value = "/ask/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    @Operation(summary = "일반 LLM 챗봇에게 질문하기(SSE)", description = "일반 LLM 챗봇에게 질문을 하고 스트리밍으로 응답을 수신합니다.")
    public SseEmitter askStream(@Valid @RequestBody AskRequest request) {
        UUID userNo = SecurityUtil.getCurrentUserUuid()
            .orElseThrow(() -> new BusinessException(ErrorCode.INVALID_ACCESS_TOKEN));
        return chatAskStreamService.askStream(userNo, null, request);
    }

    @PostMapping("/sessions/{sessionNo}/messages")
    @Operation(summary = "[관리자] 메시지 생성", description = "세션에 메시지를 추가합니다.")
    @ApiResponse(responseCode = "201", description = "메시지 생성 성공")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<BaseResponse<MessageResponse>> createMessage(
        @PathVariable UUID sessionNo,
        @Valid @RequestBody MessageCreateRequest request) {
        MessageResponse created = chatMessageService.createMessage(sessionNo, request);

        URI location = URI.create(String.format("/chat/sessions/%s/messages/%s", sessionNo,
            created.messageNo()));
        return ResponseEntity.created(location)
            .body(BaseResponse.of(HttpStatus.CREATED, created, "메시지 생성 성공"));
    }

}
