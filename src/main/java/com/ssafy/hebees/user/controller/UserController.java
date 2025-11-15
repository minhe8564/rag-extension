package com.ssafy.hebees.user.controller;

import com.ssafy.hebees.common.response.BaseResponse;
import com.ssafy.hebees.common.util.SecurityUtil;
import com.ssafy.hebees.monitoring.service.ActiveUserService;
import com.ssafy.hebees.user.dto.request.UserSignupRequest;
import com.ssafy.hebees.user.dto.response.UserInfoResponse;
import com.ssafy.hebees.user.dto.response.UserListPageResponse;
import com.ssafy.hebees.user.dto.response.UserResponse;
import com.ssafy.hebees.user.dto.response.UserSignupResponse;
import com.ssafy.hebees.user.service.UserService;
import com.ssafy.hebees.user.service.ActiveUserStreamService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.util.List;

@RestController
@RequestMapping("/user")
@RequiredArgsConstructor
@Slf4j
@Tag(name = "사용자 관리", description = "사용자 관련 API")
@Validated
public class UserController {

    private final UserService userService;
    private final ActiveUserService activeUserService;
    private final ActiveUserStreamService activeUserStreamService;

    @PostMapping("/signup")
    @Operation(summary = "회원가입", description = "새로운 사용자를 등록합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "201", description = "회원가입 성공"),
        @ApiResponse(responseCode = "400", description = "잘못된 요청(유효성 검증 실패)"),
        @ApiResponse(responseCode = "409", description = "이미 존재하는 사용자")
    })
    public ResponseEntity<BaseResponse<UserSignupResponse>> signup(
        @Valid @RequestBody UserSignupRequest request) {
        UserSignupResponse response = userService.signup(request);
        return ResponseEntity.status(HttpStatus.CREATED)
            .body(BaseResponse.of(HttpStatus.CREATED, response));
    }

    @GetMapping("/check-name")
    @Operation(summary = "이름 중복 확인", description = "사용자 이름 중복 여부를 확인합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "확인 완료"),
        @ApiResponse(responseCode = "400", description = "잘못된 요청")
    })
    public ResponseEntity<BaseResponse<Boolean>> checkName(
        @RequestParam @NotBlank(message = "이름은 필수입니다") String name) {
        boolean exists = userService.isNameExists(name);
        return ResponseEntity.ok(BaseResponse.success(exists));
    }

    @GetMapping("/check-email")
    @Operation(summary = "이메일 중복 확인", description = "사용자 이메일 중복 여부를 확인합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "확인 완료"),
        @ApiResponse(responseCode = "400", description = "잘못된 요청")
    })
    public ResponseEntity<BaseResponse<Boolean>> checkEmail(
        @RequestParam @NotBlank(message = "이메일은 필수입니다") String email) {
        boolean exists = userService.isEmailExists(email);
        return ResponseEntity.ok(BaseResponse.success(exists));
    }

    @GetMapping("/by-role")
    @Operation(summary = "역할별 사용자 조회", description = "주어진 역할명을 가진 사용자 목록을 조회합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "조회 성공"),
        @ApiResponse(responseCode = "400", description = "잘못된 요청")
    })
    public ResponseEntity<BaseResponse<List<UserResponse>>> getUsersByRole(
        @RequestParam @NotBlank(message = "역할명은 필수입니다") String roleName) {
        List<UserResponse> users = userService.getUsersByRole(roleName);
        return ResponseEntity.ok(BaseResponse.success(users));
    }

    @GetMapping("/count")
    @Operation(summary = "활성 사용자 수 조회", description = "삭제되지 않은 활성 사용자 수를 조회합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "조회 성공")
    })
    public ResponseEntity<BaseResponse<Long>> getActiveUserCount() {
        long count = userService.getActiveUserCount();
        return ResponseEntity.ok(BaseResponse.success(count));
    }

    @GetMapping("/email/{email}")
    @Operation(summary = "이메일로 사용자 조회", description = "이메일로 사용자를 조회합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "조회 성공"),
        @ApiResponse(responseCode = "404", description = "사용자를 찾을 수 없음")
    })
    public ResponseEntity<BaseResponse<UserResponse>> getUserByEmail(
        @PathVariable @NotBlank(message = "이메일은 필수입니다") String email) {
        UserResponse user = userService.getUserByEmail(email);
        return ResponseEntity.ok(BaseResponse.success(user));
    }

    @GetMapping("/name/{name}")
    @Operation(summary = "이름으로 사용자 조회", description = "이름으로 사용자를 조회합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "조회 성공"),
        @ApiResponse(responseCode = "404", description = "사용자를 찾을 수 없음")
    })
    public ResponseEntity<BaseResponse<UserResponse>> getUserByName(
        @PathVariable @NotBlank(message = "이름은 필수입니다") String name) {
        UserResponse user = userService.getUserByName(name);
        return ResponseEntity.ok(BaseResponse.success(user));
    }

    @GetMapping("/users")
    @Operation(summary = "사용자 목록 조회", description = "페이지네이션으로 사용자 목록을 조회합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "조회 성공"),
        @ApiResponse(responseCode = "400", description = "잘못된 요청")
    })
    public ResponseEntity<BaseResponse<UserListPageResponse>> getUsers(
        @RequestParam(name = "pageNum", defaultValue = "1")
        @jakarta.validation.constraints.Min(value = 1, message = "페이지 번호는 1이상이어야 합니다.") int pageNum,
        @RequestParam(name = "pageSize", defaultValue = "20")
        @jakarta.validation.constraints.Min(value = 1, message = "페이지 당 항목 수는 1이상이어야 합니다.") int pageSize
    ) {
        UserListPageResponse response = userService.getUsers(pageNum, pageSize);
        return ResponseEntity.ok(BaseResponse.success(response));
    }

    @GetMapping("/me")
    @Operation(summary = "내 정보 조회", description = "현재 로그인한 사용자의 정보를 조회합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "조회 성공"),
        @ApiResponse(responseCode = "401", description = "인증되지 않은 사용자")
    })
    public ResponseEntity<BaseResponse<UserInfoResponse>> getMyInfo() {
        var userUuid = SecurityUtil.getCurrentUserUuid()
            .orElseThrow(() -> new RuntimeException("인증된 사용자가 없습니다."));
        var user = userService.findByUuid(userUuid);
        return ResponseEntity.ok(BaseResponse.success(UserInfoResponse.of(user)));
    }

    @GetMapping(value = "/active/realtime", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    @Operation(
        summary = "실시간 활성 사용자 수 SSE 스트리밍",
        description = "최근 5분 내 활동이 있는 실시간 활성 사용자 수를 SSE로 스트리밍합니다. 활성 사용자 수가 변경될 때마다 업데이트됩니다."
    )
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "SSE 연결 성공")
    })
    public SseEmitter subscribeActiveUsersSSE(
        @RequestHeader(name = "Last-Event-ID", required = false) String lastEventId
    ) {
        return activeUserStreamService.subscribeActiveUsers(lastEventId);
    }
}

