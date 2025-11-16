package com.ssafy.hebees.llmKey.controller;

import com.ssafy.hebees.common.dto.ListResponse;
import com.ssafy.hebees.common.exception.BusinessException;
import com.ssafy.hebees.common.exception.ErrorCode;
import com.ssafy.hebees.common.response.BaseResponse;
import com.ssafy.hebees.common.util.SecurityUtil;
import com.ssafy.hebees.llmKey.dto.request.LlmKeyCreateRequest;
import com.ssafy.hebees.llmKey.dto.request.LlmKeyUpsertRequest;
import com.ssafy.hebees.llmKey.dto.response.LlmKeyResponse;
import com.ssafy.hebees.llmKey.service.LlmKeyService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import java.net.URI;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@Slf4j
@Validated
@RestController
@RequiredArgsConstructor
@RequestMapping({"/rag-settings/llm-keys/me"})
@Tag(name = "내 LLM Key 관리", description = "내 LLM Key API")
public class LlmKeyController {

    private final LlmKeyService llmKeyService;

    @GetMapping()
    @Operation(summary = "내 LLM Key 목록 조회", description = "현재 사용자의 모든 LLM Key를 조회합니다.")
    @ApiResponse(responseCode = "200", description = "내 LLM Key 목록 조회 성공")
    public ResponseEntity<BaseResponse<ListResponse<LlmKeyResponse>>> listMyLlmKeys() {
        UUID userNo = getCurrentUserUuid();
        ListResponse<LlmKeyResponse> responses = llmKeyService.listLlmKeys(userNo);
        return ResponseEntity.ok(
            BaseResponse.of(HttpStatus.OK, responses, "내 LLM Key 목록이 성공적으로 조회되었습니다."));
    }

    @GetMapping("/{llm}")
    @Operation(summary = "내 LLM Key 단건 조회", description = "LLM 이름 또는 ID로 현재 사용자의 LLM Key를 조회합니다.")
    @ApiResponse(responseCode = "200", description = "내 LLM Key 조회 성공")
    public ResponseEntity<BaseResponse<LlmKeyResponse>> getMyLlmKeyByLlm(
        @Parameter(description = "LLM 이름 또는 ID", example = "gpt-4o", required = true)
        @PathVariable("llm") String llmIdentifier
    ) {
        UUID userNo = getCurrentUserUuid();
        LlmKeyResponse response = llmKeyService.getLlmKey(userNo, llmIdentifier);
        return ResponseEntity.ok(
            BaseResponse.of(HttpStatus.OK, response, "내 LLM Key가 성공적으로 조회되었습니다."));
    }

    @PostMapping()
    @Operation(summary = "내 LLM Key 생성", description = "현재 로그인한 사용자 계정에 LLM Key를 등록합니다.")
    @ApiResponse(responseCode = "201", description = "내 LLM Key 생성 성공")
    public ResponseEntity<BaseResponse<LlmKeyResponse>> createMyLlmKey(
        @Valid @RequestBody LlmKeyCreateRequest request) {
        UUID userNo = getCurrentUserUuid();
        LlmKeyResponse response = llmKeyService.createLlmKey(userNo, request);
        return ResponseEntity.created(
                URI.create(String.format("/rag-settings/llm-keys/%s", response.llmKeyNo())))
            .body(BaseResponse.of(HttpStatus.CREATED, response, "내 LLM Key가 성공적으로 생성되었습니다."));
    }

    @PutMapping("/{llm}")
    @Operation(summary = "내 LLM Key 수정", description = "현재 사용자 계정에 등록된 LLM Key를 수정합니다.")
    @ApiResponse(responseCode = "200", description = "내 LLM Key 수정 성공")
    public ResponseEntity<BaseResponse<LlmKeyResponse>> updateMyLlmKey(
        @Parameter(description = "LLM 이름 또는 ID", example = "1cb9d767-0a5f-4cda-9be9-7428c9af5c42", required = true)
        @PathVariable("llm") String llmIdentifier,
        @Valid @RequestBody LlmKeyUpsertRequest request) {
        UUID userNo = getCurrentUserUuid();
        LlmKeyResponse response = llmKeyService.upsertLlmKey(userNo, llmIdentifier, request);
        return ResponseEntity.ok(
            BaseResponse.of(HttpStatus.OK, response, "내 LLM Key가 성공적으로 수정되었습니다."));
    }

    @DeleteMapping("/{llm}")
    @Operation(summary = "내 LLM Key 삭제", description = "현재 사용자 계정에서 LLM Key를 삭제합니다.")
    @ApiResponse(responseCode = "204", description = "내 LLM Key 삭제 성공")
    public ResponseEntity<Void> deleteMyLlmKey(
        @Parameter(description = "LLM 이름 또는 ID", example = "GPT-4o", required = true)
        @PathVariable("llm") String llmIdentifier) {
        UUID userNo = getCurrentUserUuid();
        llmKeyService.deleteLlmKey(userNo, llmIdentifier);
        return ResponseEntity.noContent().build();
    }

    private UUID getCurrentUserUuid() {
        return SecurityUtil.getCurrentUserUuid()
            .orElseThrow(() -> new BusinessException(ErrorCode.INVALID_ACCESS_TOKEN));
    }
}
