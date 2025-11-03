package com.ssafy.hebees.chat.controller;

import com.ssafy.hebees.chat.dto.request.SessionCreateRequest;
import com.ssafy.hebees.chat.dto.request.SessionListRequest;
import com.ssafy.hebees.chat.dto.request.SessionUpdateRequest;
import com.ssafy.hebees.chat.dto.response.SessionCreateResponse;
import com.ssafy.hebees.chat.dto.response.SessionResponse;
import com.ssafy.hebees.chat.service.ChatService;
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
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import java.net.URI;
import java.util.List;
import java.util.UUID;


@RestController
@RequestMapping("/chat")
@RequiredArgsConstructor
@Slf4j
@Tag(name = "채팅 관리", description = "채팅 관련 API")
@Validated
public class ChatController {

    private final ChatService chatService;

    @GetMapping("/sessions")
    @Operation(summary = "세션 목록 조회", description = "세션 목록을 조회합니다.")
    @ApiResponses({
            @ApiResponse(responseCode = "200", description = "세션 목록 조회 성공"),
    })
    public ResponseEntity<BaseResponse<PageResponse<SessionResponse>>> listSessions (
            @Valid @ModelAttribute PageRequest pageRequest,
            @Valid@ModelAttribute SessionListRequest listRequest
    ) {
        UUID userNo = SecurityUtil.getCurrentUserUuid().orElseThrow(()->new BusinessException(ErrorCode.INVALID_ACCESS_TOKEN));
        PageResponse<SessionResponse> sessions = chatService.getSessions(userNo, pageRequest, listRequest);

        return ResponseEntity.ok(BaseResponse.of(HttpStatus.OK, sessions));
    }

    @GetMapping("/sessions/{sessionNo}")
    @Operation(summary = "세션 조회", description = "세션을 조회합니다.")
    @ApiResponses({
            @ApiResponse(responseCode = "200", description = "세션 조회 성공"),
    })
    public ResponseEntity<BaseResponse<SessionResponse>> getSession (@PathVariable UUID sessionNo) {
        UUID userNo = SecurityUtil.getCurrentUserUuid().orElseThrow(()->new BusinessException(ErrorCode.INVALID_ACCESS_TOKEN));
        SessionResponse session = chatService.getSession(userNo, sessionNo);

        return ResponseEntity.ok(BaseResponse.of(HttpStatus.OK, session));
    }

    @PostMapping("/sessions")
    @Operation(summary = "세션 생성", description = "새로운 세션을 생성합니다.")
    @ApiResponses({
            @ApiResponse(responseCode = "201", description = "세션 생성 성공"),
            @ApiResponse(responseCode = "400", description = "잘못된 요청 (유효성 검사 실패)"),
    })
    public ResponseEntity<BaseResponse<SessionCreateResponse>> createSession (@Valid SessionCreateRequest request) {
        UUID userNo = SecurityUtil.getCurrentUserUuid().orElseThrow(()->new BusinessException(ErrorCode.INVALID_ACCESS_TOKEN));
        SessionCreateResponse session = chatService.createSession(userNo, request);

        UUID sessionNo = session.sessionNo();
        URI location = URI.create("/sessions/"+sessionNo);
        return ResponseEntity.created(location).body(BaseResponse.of(HttpStatus.CREATED, new SessionCreateResponse(sessionNo), "세션 생성에 성공하였습니다."));
    }


    @PutMapping("/sessions/{sessionNo}")
    @Operation(summary = "세션 수정", description = "세션 정보를 수정합니다.")
    @ApiResponses({
            @ApiResponse(responseCode = "200", description = "세션 정보 수정 성공"),
            @ApiResponse(responseCode = "400", description = "잘못된 요청 (유효성 검사 실패)"),
    })
    public ResponseEntity<BaseResponse<Void>> updateSession (@PathVariable UUID sessionNo, @Valid SessionUpdateRequest request) {
        UUID userNo = SecurityUtil.getCurrentUserUuid().orElseThrow(()->new BusinessException(ErrorCode.INVALID_ACCESS_TOKEN));
        chatService.updateSession(userNo, sessionNo, request);

        return ResponseEntity.ok(BaseResponse.of(HttpStatus.OK, null, "세션 수정에 성공하였습니다."));
    }

    @DeleteMapping("/sessions/{sessionNo}")
    @Operation(summary = "세션 삭제", description = "세션을 삭제합니다.")
    @ApiResponses({
            @ApiResponse(responseCode = "204", description = "세션 삭제 성공"),
    })
    public ResponseEntity<Void> deleteSession (@PathVariable UUID sessionNo) {
        UUID userNo = SecurityUtil.getCurrentUserUuid().orElseThrow(()->new BusinessException(ErrorCode.INVALID_ACCESS_TOKEN));
        chatService.deleteSession(userNo, sessionNo);

        return ResponseEntity.noContent().build();
    }

    @GetMapping("/sessions/{sessionNo}/messages")
    @Operation(summary = "메시지 목록 조회", description = "메시지 목록을 조회합니다.")
    @ApiResponses({
            @ApiResponse(responseCode = "200", description = "메시지 목록 조회 성공"),
    })
    public ResponseEntity<Void> listSessionMessages (@PathVariable UUID sessionNo) {
        return ResponseEntity.ok().build();
    }

    @GetMapping("/sessions/{sessionNo}/messages/{messageNo}")
    @Operation(summary = "메시지 조회", description = "메시지를 조회합니다.")
    @ApiResponses({
            @ApiResponse(responseCode = "200", description = "메시지 조회 성공"),
    })
    public ResponseEntity<Void> getMessage (@PathVariable UUID sessionNo, @PathVariable UUID messageNo) {
        return ResponseEntity.status(HttpStatus.NOT_IMPLEMENTED).build();
    }

    @GetMapping("/sessions/{sessionNo}/messages/{messageNo}/documents")
    @Operation(summary = "참조 문서 목록 조회", description = "참조된 문서의 목록을 조회합니다.")
    @ApiResponses({
            @ApiResponse(responseCode = "200", description = "참조 문서 목록 조회 성공."),
    })
    public ResponseEntity<Void> listReferencedDocuments (@PathVariable UUID sessionNo, @PathVariable UUID messageNo) {
        return ResponseEntity.status(HttpStatus.NOT_IMPLEMENTED).build();
    }

    @GetMapping("/sessions/{sessionNo}/messages/{messageNo}/documents/{documentNo}")
    @Operation(summary = "참조 문서 목록 조회", description = "참조된 문서를 조회합니다.")
    @ApiResponses({
            @ApiResponse(responseCode = "200", description = "참조 문서 조회 성공."),
    })
    public ResponseEntity<Void> listReferencedDocuments (@PathVariable UUID sessionNo, @PathVariable UUID messageNo, @PathVariable UUID documentNo) {
        return ResponseEntity.status(HttpStatus.NOT_IMPLEMENTED).build();
    }
}
