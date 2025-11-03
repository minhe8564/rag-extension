package com.ssafy.hebees.user.controller;

import com.ssafy.hebees.user.dto.request.UserRoleUpsertRequest;
import com.ssafy.hebees.user.dto.response.UserRoleCreateResponse;
import com.ssafy.hebees.user.dto.response.UserRoleResponse;
import com.ssafy.hebees.user.entity.UserRole;
import com.ssafy.hebees.user.service.UserRoleService;
import com.ssafy.hebees.common.dto.ListResponse;
import com.ssafy.hebees.common.response.BaseResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;

import java.net.URI;
import java.util.List;
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

@RestController
@RequestMapping("/user/roles")
@RequiredArgsConstructor
@Slf4j
@Tag(name = "사용자 권한", description = "사용자 권한 API")
@Validated
public class UserRoleController {

    private final UserRoleService userRoleService;

    @GetMapping
    @Operation(summary = "사용자 역할 목록 조회", description = "등록된 모든 사용자 역할을 조회합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "조회 성공")
    })
    public ResponseEntity<BaseResponse<ListResponse<UserRoleResponse>>> listRole() {
        log.info("사용자 역할 목록 조회 요청");

        List<UserRoleResponse> roles = userRoleService.getRoles().stream()
            .map(UserRoleResponse::from)
            .toList();

        return ResponseEntity.ok(BaseResponse.success(new ListResponse<>(roles)));
    }

    @GetMapping("/{userRoleNo}")
    @Operation(summary = "사용자 역할 상세 조회", description = "사용자 역할을 식별자로 조회합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "조회 성공"),
        @ApiResponse(responseCode = "404", description = "역할을 찾을 수 없음")
    })
    public ResponseEntity<BaseResponse<UserRoleResponse>> getRole(
        @PathVariable UUID userRoleNo) {
        log.info("사용자 역할 조회 요청: {}", userRoleNo);

        UserRole role = userRoleService.getRole(userRoleNo);
        return ResponseEntity.ok(BaseResponse.of(HttpStatus.OK, UserRoleResponse.from(role), "역할 조회에 성공하였습니다."));
    }

    @PostMapping
    @Operation(summary = "사용자 역할 생성", description = "새로운 사용자 역할을 생성합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "201", description = "생성 성공"),
        @ApiResponse(responseCode = "400", description = "잘못된 요청"),
        @ApiResponse(responseCode = "409", description = "이미 존재하는 역할")
    })
    public ResponseEntity<BaseResponse<UserRoleCreateResponse>> addRole(
        @Valid @RequestBody UserRoleUpsertRequest request) {
        log.info("사용자 역할 생성 요청: {}", request.name());

        UserRole created = userRoleService.createRole(request);
        return ResponseEntity.created(URI.create("/user/roles/"+created.getUuid()))
                .body(BaseResponse.of(HttpStatus.CREATED, UserRoleCreateResponse.from(created), "사용자 역할 생성에 성공하였습니다."));
    }

    @DeleteMapping("/{userRoleNo}")
    @Operation(summary = "사용자 역할 삭제", description = "사용자 역할을 삭제합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "204", description = "삭제 성공"),
        @ApiResponse(responseCode = "404", description = "역할을 찾을 수 없음"),
        @ApiResponse(responseCode = "409", description = "사용 중인 역할")
    })
    public ResponseEntity<BaseResponse<String>> deleteRole(@PathVariable UUID userRoleNo) {
        log.info("사용자 역할 삭제 요청: {}", userRoleNo);

        userRoleService.deleteRole(userRoleNo);
        return ResponseEntity.noContent().build();
    }

    @PutMapping("/{userRoleNo}")
    @Operation(summary = "사용자 역할 수정", description = "사용자 역할 정보를 수정합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "수정 성공"),
        @ApiResponse(responseCode = "400", description = "잘못된 요청"),
        @ApiResponse(responseCode = "404", description = "역할을 찾을 수 없음"),
        @ApiResponse(responseCode = "409", description = "이미 존재하는 역할")
    })
    public ResponseEntity<BaseResponse<Void>> updateRole(@PathVariable UUID userRoleNo,
        @Valid @RequestBody UserRoleUpsertRequest request) {
        log.info("사용자 역할 수정 요청: {}", userRoleNo);

        userRoleService.updateRole(userRoleNo, request);
        return ResponseEntity.ok(
            BaseResponse.of(HttpStatus.OK, null, "사용자 역할 수정에 성공하였습니다."));
    }
}
