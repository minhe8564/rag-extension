package com.ssafy.hebees.ragsetting.controller;

import com.ssafy.hebees.common.dto.ListResponse;
import com.ssafy.hebees.common.exception.BusinessException;
import com.ssafy.hebees.common.exception.ErrorCode;
import com.ssafy.hebees.common.response.BaseResponse;
import com.ssafy.hebees.common.util.SecurityUtil;
import com.ssafy.hebees.ragsetting.dto.request.LlmKeyCreateRequest;
import com.ssafy.hebees.ragsetting.dto.request.LlmKeySelfCreateRequest;
import com.ssafy.hebees.ragsetting.dto.request.LlmKeySelfUpdateRequest;
import com.ssafy.hebees.ragsetting.dto.request.LlmKeyUpdateRequest;
import com.ssafy.hebees.ragsetting.dto.response.LlmKeyResponse;
import com.ssafy.hebees.ragsetting.service.LlmKeyService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
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
import org.springframework.util.StringUtils;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@Slf4j
@Validated
@RestController
@RequiredArgsConstructor
@RequestMapping("/rag-settings/llm-keys")
@Tag(name = "LLM Key 관리", description = "LLM Key CRUD API")
public class LlmKeyController {

    private final LlmKeyService llmKeyService;

    @PostMapping
    @Operation(summary = "[관리자] LLM Key 생성", description = "새로운 LLM Key를 등록합니다.")
    @ApiResponse(responseCode = "201", description = "LLM Key 생성 성공",
        content = @Content(schema = @Schema(implementation = LlmKeyResponse.class)))
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<BaseResponse<LlmKeyResponse>> createLlmKey(
        @Valid @RequestBody LlmKeyCreateRequest request) {
        LlmKeyResponse response = llmKeyService.create(request);
        URI location = URI.create("/rag-settings/llm-keys/" + response.llmKeyNo());
        return ResponseEntity.created(location)
            .body(BaseResponse.of(HttpStatus.CREATED, response, "LLM Key 생성에 성공하였습니다."));
    }

    @GetMapping("/{llmKeyNo}")
    @Operation(summary = "[관리자]  LLM Key 단건 조회", description = "LLM Key 상세 정보를 조회합니다.")
    @ApiResponse(responseCode = "200", description = "LLM Key 조회 성공",
        content = @Content(schema = @Schema(implementation = LlmKeyResponse.class)))
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<BaseResponse<LlmKeyResponse>> getLlmKey(
        @PathVariable UUID llmKeyNo) {
        LlmKeyResponse response = llmKeyService.get(llmKeyNo);
        return ResponseEntity.ok(
            BaseResponse.of(HttpStatus.OK, response, "LLM Key 조회에 성공하였습니다."));
    }

    @GetMapping
    @Operation(summary = "[관리자] LLM Key 목록 조회", description = "등록된 LLM Key 목록을 조회합니다.")
    @ApiResponse(responseCode = "200", description = "LLM Key 목록 조회 성공",
        content = @Content(schema = @Schema(implementation = LlmKeyResponse.class)))
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<BaseResponse<ListResponse<LlmKeyResponse>>> listLlmKeys(
        @Parameter(description = "사용자 ID로 필터링", example = "6d3efc39-d052-49a2-8d16-31a8a99f8889")
        @RequestParam(name = "userNo", required = false) UUID userNo) {
        ListResponse<LlmKeyResponse> responses = llmKeyService.list(userNo);
        return ResponseEntity.ok(
            BaseResponse.of(HttpStatus.OK, responses, "LLM Key 목록 조회에 성공하였습니다."));
    }

    @PutMapping("/{llmKeyNo}")
    @Operation(summary = "[관리자] LLM Key 수정", description = "LLM Key 정보를 수정합니다.")
    @ApiResponse(responseCode = "200", description = "LLM Key 수정 성공",
        content = @Content(schema = @Schema(implementation = LlmKeyResponse.class)))
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<BaseResponse<LlmKeyResponse>> updateLlmKey(
        @PathVariable UUID llmKeyNo,
        @Valid @RequestBody LlmKeyUpdateRequest request) {
        LlmKeyResponse response = llmKeyService.update(llmKeyNo, request);
        return ResponseEntity.ok(
            BaseResponse.of(HttpStatus.OK, response, "LLM Key 수정에 성공하였습니다."));
    }

    @DeleteMapping("/{llmKeyNo}")
    @Operation(summary = "[관리자] LLM Key 삭제", description = "LLM Key를 삭제합니다.")
    @ApiResponse(responseCode = "204", description = "LLM Key 삭제 성공")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<Void> deleteLlmKey(@PathVariable UUID llmKeyNo) {
        llmKeyService.delete(llmKeyNo);
        return ResponseEntity.noContent().build();
    }

    @PostMapping("/me")
    @Operation(summary = "내 LLM Key 생성", description = "현재 사용자 계정으로 LLM Key를 등록합니다.")
    @ApiResponse(responseCode = "201", description = "LLM Key 생성 성공",
        content = @Content(schema = @Schema(implementation = LlmKeyResponse.class)))
    public ResponseEntity<BaseResponse<LlmKeyResponse>> createMyLlmKey(
        @Valid @RequestBody LlmKeySelfCreateRequest request) {
        UUID userNo = currentUser();
        LlmKeyResponse response = llmKeyService.createSelf(userNo, request);
        URI location = URI.create(String.format("/rag-settings/llm-keys/%s", response.llmKeyNo()));
        return ResponseEntity.created(location)
            .body(BaseResponse.of(HttpStatus.CREATED, response, "LLM Key 생성에 성공하였습니다."));
    }

    @GetMapping("/me")
    @Operation(summary = "내 LLM Key 목록 조회", description = "현재 사용자의 LLM Key 목록을 조회합니다.")
    @ApiResponse(responseCode = "200", description = "LLM Key 목록 조회 성공",
        content = @Content(schema = @Schema(implementation = LlmKeyResponse.class)))
    public ResponseEntity<BaseResponse<ListResponse<LlmKeyResponse>>> listMyLlmKeys() {
        UUID userNo = currentUser();
        ListResponse<LlmKeyResponse> responses = llmKeyService.listSelf(userNo);
        return ResponseEntity.ok(
            BaseResponse.of(HttpStatus.OK, responses, "LLM Key 목록 조회에 성공하였습니다."));
    }

    @GetMapping("/me/{llmName}")
    @Operation(summary = "내 LLM Key 단건 조회", description = "LLM 이름으로 현재 사용자의 LLM Key를 조회합니다.")
    @ApiResponse(responseCode = "200", description = "LLM Key 조회 성공",
        content = @Content(schema = @Schema(implementation = LlmKeyResponse.class)))
    public ResponseEntity<BaseResponse<LlmKeyResponse>> getMyLlmKeyByLlm(
        @Parameter(description = "LLM 이름", example = "gpt-4o", required = true)
        @PathVariable("llmName") String llmName
    ) {
        UUID userNo = currentUser();
        String validated = requireLlmName(llmName);
        LlmKeyResponse response = llmKeyService.getSelfByLlm(userNo, validated);
        return ResponseEntity.ok(
            BaseResponse.of(HttpStatus.OK, response, "LLM Key 조회에 성공하였습니다."));
    }

    @PutMapping("/me/{llmName}")
    @Operation(summary = "내 LLM Key 수정", description = "현재 사용자 계정의 LLM Key를 수정합니다.")
    @ApiResponse(responseCode = "200", description = "LLM Key 수정 성공",
        content = @Content(schema = @Schema(implementation = LlmKeyResponse.class)))
    public ResponseEntity<BaseResponse<LlmKeyResponse>> updateMyLlmKey(
        @Parameter(description = "LLM 이름", example = "gpt-4o", required = true)
        @PathVariable("llmName") String llmName,
        @Valid @RequestBody LlmKeySelfUpdateRequest request) {
        UUID userNo = currentUser();
        String validated = requireLlmName(llmName);
        LlmKeyResponse response = llmKeyService.updateSelf(userNo, validated, request);
        return ResponseEntity.ok(
            BaseResponse.of(HttpStatus.OK, response, "LLM Key 수정에 성공하였습니다."));
    }

    @DeleteMapping("/me/{llmName}")
    @Operation(summary = "내 LLM Key 삭제", description = "현재 사용자 계정의 LLM Key를 삭제합니다.")
    @ApiResponse(responseCode = "204", description = "LLM Key 삭제 성공")
    public ResponseEntity<Void> deleteMyLlmKey(
        @Parameter(description = "LLM 이름", example = "gpt-4o", required = true)
        @PathVariable("llmName") String llmName) {
        UUID userNo = currentUser();
        String validated = requireLlmName(llmName);
        llmKeyService.deleteSelf(userNo, validated);
        return ResponseEntity.noContent().build();
    }

    private UUID currentUser() {
        return SecurityUtil.getCurrentUserUuid()
            .orElseThrow(() -> new BusinessException(ErrorCode.INVALID_ACCESS_TOKEN));
    }

    private String requireLlmName(String llmName) {
        String trimmed = llmName != null ? llmName.trim() : null;
        if (!StringUtils.hasText(trimmed)) {
            throw new BusinessException(ErrorCode.BAD_REQUEST);
        }
        try {
            UUID.fromString(trimmed);
            throw new BusinessException(ErrorCode.BAD_REQUEST);
        } catch (IllegalArgumentException ignored) {
        }
        return trimmed;
    }
}


