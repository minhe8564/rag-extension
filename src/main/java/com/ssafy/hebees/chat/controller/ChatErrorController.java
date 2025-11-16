package com.ssafy.hebees.chat.controller;

import com.ssafy.hebees.chat.dto.request.MessageErrorCreateRequest;
import com.ssafy.hebees.chat.dto.request.MessageErrorSearchRequest;
import com.ssafy.hebees.chat.dto.response.MessageErrorCreateResponse;
import com.ssafy.hebees.chat.dto.response.MessageErrorResponse;
import com.ssafy.hebees.chat.service.MessageErrorService;
import com.ssafy.hebees.common.dto.PageRequest;
import com.ssafy.hebees.common.dto.PageResponse;
import com.ssafy.hebees.common.response.BaseResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import java.net.URI;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/chat")
@RequiredArgsConstructor
@Slf4j
@Tag(name = "채팅 에러 관리", description = "채팅 에러 관련 API")
@PreAuthorize("hasRole('ADMIN')")
public class ChatErrorController {

    private final MessageErrorService messageErrorService;

    @PostMapping("/errors")
    @Operation(summary = "채팅 에러 내역 등록하기", description = "채팅 에러 내역을 등록합니다.")
    @ApiResponse(responseCode = "201", description = "채팅 에러 내역 등록에 성공하였습니다.")
    public ResponseEntity<BaseResponse<MessageErrorCreateResponse>> createMessageError(
        @Valid @RequestBody MessageErrorCreateRequest request) {

        MessageErrorCreateResponse response = messageErrorService.createError(request);

        return ResponseEntity.created(
                URI.create(String.format("/chat/errors/%s", response.messageErrorNo())))
            .body(BaseResponse.of(HttpStatus.CREATED, response, "에러 메시지 등록에 성공하였습니다."));
    }

    @GetMapping("/errors")
    @Operation(summary = "[관리자] 채팅 에러 내역 목록 조회하기", description = "채팅 에러 내역 목록을 조회합니다.")
    @ApiResponse(responseCode = "200", description = "채팅 에러 내역 목록 조회에 성공하였습니다.")
    public ResponseEntity<BaseResponse<PageResponse<MessageErrorResponse>>> listMessageError(
        @Valid @ModelAttribute PageRequest pageRequest,
        @Valid @ModelAttribute MessageErrorSearchRequest searchRequest
    ) {
        PageResponse<MessageErrorResponse> errors = messageErrorService.listErrors(
            pageRequest, searchRequest);

        return ResponseEntity.ok(
            BaseResponse.of(HttpStatus.OK, errors, "채팅 에러 내역 목록 조회에 성공하였습니다.")
        );
    }

    @DeleteMapping("/errors/{errorNo}")
    @Operation(summary = "[관리자] 채팅 에러 내역 삭제하기", description = "채팅 에러 내역을 삭제합니다.")
    @ApiResponse(responseCode = "204", description = "채팅 에러 내역 삭제에 성공하였습니다.")
    public ResponseEntity<Void> deleteMessageError(@PathVariable UUID errorNo) {
        messageErrorService.deleteError(errorNo);
        return ResponseEntity.noContent().build();
    }

}
