package com.ssafy.hebees.chat.controller;

import com.ssafy.hebees.chat.dto.request.AskRequest;
import com.ssafy.hebees.chat.dto.request.MessageCreateRequest;
import com.ssafy.hebees.chat.dto.request.MessageCursorRequest;
import com.ssafy.hebees.chat.dto.request.SessionCreateRequest;
import com.ssafy.hebees.chat.dto.request.SessionListRequest;
import com.ssafy.hebees.chat.dto.request.SessionUpdateRequest;
import com.ssafy.hebees.chat.dto.response.AskResponse;
import com.ssafy.hebees.chat.dto.response.MessageCursorResponse;
import com.ssafy.hebees.chat.dto.response.MessageResponse;
import com.ssafy.hebees.chat.dto.response.ReferencedDocumentListResponse;
import com.ssafy.hebees.chat.dto.response.ReferencedDocumentResponse;
import com.ssafy.hebees.chat.dto.response.SessionCreateResponse;
import com.ssafy.hebees.chat.dto.response.SessionResponse;
import com.ssafy.hebees.chat.service.ChatService;
import com.ssafy.hebees.chat.service.MessageService;
import com.ssafy.hebees.common.dto.PageRequest;
import com.ssafy.hebees.common.dto.PageResponse;
import com.ssafy.hebees.common.exception.BusinessException;
import com.ssafy.hebees.common.exception.ErrorCode;
import com.ssafy.hebees.common.response.BaseResponse;
import com.ssafy.hebees.common.util.SecurityUtil;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import java.net.URI;
import java.time.LocalDateTime;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;


@RestController
@RequestMapping("/chat")
@RequiredArgsConstructor
@Slf4j
@Tag(name = "채팅 관리", description = "채팅 관련 API")
@Validated
public class ChatController {

    private final ChatService chatService;
    private final MessageService chatMessageService;

    @GetMapping("/sessions")
    @Operation(summary = "세션 목록 조회", description = "세션 목록을 조회합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "세션 목록 조회 성공"),
    })
    public ResponseEntity<BaseResponse<PageResponse<SessionResponse>>> listSessions(
        @Valid @ModelAttribute PageRequest pageRequest,
        @Valid @ModelAttribute SessionListRequest listRequest
    ) {
        UUID userNo = SecurityUtil.getCurrentUserUuid()
            .orElseThrow(() -> new BusinessException(ErrorCode.INVALID_ACCESS_TOKEN));
        PageResponse<SessionResponse> sessions = chatService.getSessions(userNo, pageRequest,
            listRequest);

        return ResponseEntity.ok(BaseResponse.of(HttpStatus.OK, sessions));
    }

    @GetMapping("/sessions/{sessionNo}")
    @Operation(summary = "세션 조회", description = "세션을 조회합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "세션 조회 성공"),
    })
    public ResponseEntity<BaseResponse<SessionResponse>> getSession(@PathVariable UUID sessionNo) {
        UUID userNo = SecurityUtil.getCurrentUserUuid()
            .orElseThrow(() -> new BusinessException(ErrorCode.INVALID_ACCESS_TOKEN));
        SessionResponse session = chatService.getSession(userNo, sessionNo);

        return ResponseEntity.ok(BaseResponse.of(HttpStatus.OK, session));
    }

    @PostMapping("/sessions")
    @Operation(summary = "세션 생성", description = "새로운 세션을 생성합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "201", description = "세션 생성 성공"),
        @ApiResponse(responseCode = "400", description = "잘못된 요청 (유효성 검사 실패)"),
    })
    public ResponseEntity<BaseResponse<SessionCreateResponse>> createSession(
        @Valid SessionCreateRequest request) {
        UUID userNo = SecurityUtil.getCurrentUserUuid()
            .orElseThrow(() -> new BusinessException(ErrorCode.INVALID_ACCESS_TOKEN));
        SessionCreateResponse session = chatService.createSession(userNo, request);

        UUID sessionNo = session.sessionNo();
        URI location = URI.create("/sessions/" + sessionNo);
        return ResponseEntity.created(location).body(
            BaseResponse.of(HttpStatus.CREATED, new SessionCreateResponse(sessionNo),
                "세션 생성에 성공하였습니다."));
    }


    @PutMapping("/sessions/{sessionNo}")
    @Operation(summary = "세션 수정", description = "세션 정보를 수정합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "세션 정보 수정 성공"),
        @ApiResponse(responseCode = "400", description = "잘못된 요청 (유효성 검사 실패)"),
    })
    public ResponseEntity<BaseResponse<Void>> updateSession(@PathVariable UUID sessionNo,
        @Valid SessionUpdateRequest request) {
        UUID userNo = SecurityUtil.getCurrentUserUuid()
            .orElseThrow(() -> new BusinessException(ErrorCode.INVALID_ACCESS_TOKEN));
        chatService.updateSession(userNo, sessionNo, request);

        return ResponseEntity.ok(BaseResponse.of(HttpStatus.OK, null, "세션 수정에 성공하였습니다."));
    }

    @DeleteMapping("/sessions/{sessionNo}")
    @Operation(summary = "세션 삭제", description = "세션을 삭제합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "204", description = "세션 삭제 성공"),
    })
    public ResponseEntity<Void> deleteSession(@PathVariable UUID sessionNo) {
        UUID userNo = SecurityUtil.getCurrentUserUuid()
            .orElseThrow(() -> new BusinessException(ErrorCode.INVALID_ACCESS_TOKEN));
        chatService.deleteSession(userNo, sessionNo);

        return ResponseEntity.noContent().build();
    }

    @PostMapping("/sessions/{sessionNo}/messages")
    @Operation(summary = "[TEST] 메시지 생성", description = "세션에 메시지를 추가합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "201", description = "메시지 생성 성공"),
    })
    public ResponseEntity<BaseResponse<MessageResponse>> createMessage(
        @PathVariable UUID sessionNo,
        @Valid @RequestBody MessageCreateRequest request) {
        UUID userNo = SecurityUtil.getCurrentUserUuid()
            .orElseThrow(() -> new BusinessException(ErrorCode.INVALID_ACCESS_TOKEN));
        MessageResponse created = chatMessageService.createMessage(userNo, sessionNo, request);

        URI location = URI.create(String.format("/chat/sessions/%s/messages/%s", sessionNo,
            created.messageNo()));
        return ResponseEntity.created(location)
            .body(BaseResponse.of(HttpStatus.CREATED, created, "메시지 생성 성공"));
    }

    @GetMapping("/sessions/{sessionNo}/messages")
    @Operation(summary = "메시지 목록 조회", description = "메시지 목록을 조회합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "메시지 목록 조회 성공"),
    })
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
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "메시지 조회 성공"),
    })
    public ResponseEntity<BaseResponse<MessageResponse>> getMessage(
        @PathVariable UUID sessionNo, @PathVariable UUID messageNo) {
        UUID userNo = SecurityUtil.getCurrentUserUuid()
            .orElseThrow(() -> new BusinessException(ErrorCode.INVALID_ACCESS_TOKEN));
        MessageResponse message = chatMessageService.getMessage(userNo, sessionNo, messageNo);
        return ResponseEntity.ok(BaseResponse.of(HttpStatus.OK, message, "메시지 조회 성공"));
    }

    @GetMapping("/sessions/{sessionNo}/messages/{messageNo}/documents")
    @Operation(summary = "참조 문서 목록 조회", description = "참조된 문서의 목록을 조회합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "참조 문서 목록 조회 성공."),
    })
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
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "참조 문서 조회 성공."),
    })
    public ResponseEntity<BaseResponse<ReferencedDocumentResponse>> getReferencedDocument(
        @PathVariable UUID sessionNo, @PathVariable UUID messageNo, @PathVariable UUID documentNo) {
        UUID userNo = SecurityUtil.getCurrentUserUuid()
            .orElseThrow(() -> new BusinessException(ErrorCode.INVALID_ACCESS_TOKEN));
        ReferencedDocumentResponse document = chatMessageService.getReferencedDocument(userNo,
            sessionNo, messageNo, documentNo);
        return ResponseEntity.ok(BaseResponse.of(HttpStatus.OK, document, "참조 문서 조회 성공"));
    }

    @PostMapping("/sessions/{sessionNo}/ask")
    @Operation(summary = "[임시] 질문하기", description = "챗봇에게 질문을 보냅니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "질문 성공"),
    })
    public ResponseEntity<BaseResponse<AskResponse>> ask(
        @Valid AskRequest request
    ) {
        return ResponseEntity.ok(
            BaseResponse.of(
                HttpStatus.OK,
                new AskResponse("테스트 응답", LocalDateTime.now()),
                "질문 요청에 성공하였습니다."
            ));
    }
}
