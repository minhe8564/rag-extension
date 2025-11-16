package com.ssafy.hebees.AgentPrompt.controller;

import com.ssafy.hebees.common.dto.ListResponse;
import com.ssafy.hebees.common.response.BaseResponse;
import com.ssafy.hebees.AgentPrompt.dto.requeset.AgentPromptUpsertRequest;
import com.ssafy.hebees.AgentPrompt.dto.response.AgentPromptResponse;
import com.ssafy.hebees.AgentPrompt.service.AgentPromptService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import java.net.URI;
import java.util.Objects;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequiredArgsConstructor
@RequestMapping("/agent-prompts")
@Tag(name = "Agent Prompt 관리", description = "에이전트 프롬프트 CRUD API")
@PreAuthorize("hasRole('ADMIN')")
public class AgentPromptController {

    private final AgentPromptService agentPromptService;

    @GetMapping
    @Operation(summary = "[관리자] Agent Prompt 목록 조회", description = "등록된 Agent Prompt 목록을 조회합니다.")
    @ApiResponse(responseCode = "200", description = "Agent Prompt 목록 조회 성공")
    public ResponseEntity<BaseResponse<ListResponse<AgentPromptResponse>>> listAgentPrompts() {
        ListResponse<AgentPromptResponse> responses = agentPromptService.listAgentPrompts();
        return ResponseEntity.ok(
            BaseResponse.of(HttpStatus.OK, responses, "Agent Prompt 목록 조회에 성공하였습니다."));
    }

    @GetMapping("/{agentPromptNo}")
    @Operation(summary = "[관리자] Agent Prompt 단건 조회", description = "Agent Prompt 상세 정보를 조회합니다.")
    @ApiResponse(responseCode = "200", description = "Agent Prompt 조회 성공")
    public ResponseEntity<BaseResponse<AgentPromptResponse>> getAgentPrompt(
        @PathVariable UUID agentPromptNo) {
        AgentPromptResponse response = agentPromptService.getAgentPrompt(agentPromptNo);
        return ResponseEntity.ok(
            BaseResponse.of(HttpStatus.OK, response, "Agent Prompt 조회에 성공하였습니다."));
    }

    @PostMapping
    @Operation(summary = "[관리자] Agent Prompt 생성", description = "새로운 Agent Prompt를 등록합니다.")
    @ApiResponse(responseCode = "201", description = "Agent Prompt 생성 성공")
    public ResponseEntity<BaseResponse<AgentPromptResponse>> createAgentPrompt(
        @Valid @RequestBody AgentPromptUpsertRequest request) {
        AgentPromptResponse response = agentPromptService.createAgentPrompt(request);
        URI location = URI.create(String.format("/agent-prompts/%s", response.agentPromptNo()));
        return ResponseEntity.created(location)
            .body(BaseResponse.of(HttpStatus.CREATED, response, "Agent Prompt 생성에 성공하였습니다."));
    }

    @PutMapping("/{agentPromptNo}")
    @Operation(summary = "[관리자] Agent Prompt 수정", description = "Agent Prompt 정보를 수정합니다.")
    @ApiResponse(responseCode = "200", description = "Agent Prompt 수정 성공")
    public ResponseEntity<BaseResponse<AgentPromptResponse>> updateAgentPrompt(
        @PathVariable UUID agentPromptNo,
        @Valid @RequestBody AgentPromptUpsertRequest request) {
        AgentPromptResponse response = agentPromptService.updateAgentPrompt(agentPromptNo, request);
        return ResponseEntity.ok(
            BaseResponse.of(HttpStatus.OK, response, "Agent Prompt 수정에 성공하였습니다."));
    }

    @DeleteMapping("/{agentPromptNo}")
    @Operation(summary = "[관리자] Agent Prompt 삭제", description = "Agent Prompt를 삭제합니다.")
    @ApiResponse(responseCode = "204", description = "Agent Prompt 삭제 성공")
    public ResponseEntity<Void> deleteAgentPrompt(@PathVariable UUID agentPromptNo) {
        agentPromptService.deleteAgentPrompt(agentPromptNo);
        return ResponseEntity.noContent().build();
    }
}
