package com.ssafy.hebees.user.controller;

import com.ssafy.hebees.user.dto.UserSignupRequest;
import com.ssafy.hebees.user.dto.UserSignupResponse;
import com.ssafy.hebees.user.entity.User;
import com.ssafy.hebees.user.entity.UserRole;
import com.ssafy.hebees.user.service.UserService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/user")
@RequiredArgsConstructor
@Slf4j
@Tag(name = "사용자 관리", description = "사용자 관련 API")
public class UserController {

    private final UserService userService;

    @PostMapping("/signup")
    @Operation(summary = "회원가입", description = "새로운 사용자를 등록합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "201", description = "회원가입 성공"),
        @ApiResponse(responseCode = "400", description = "잘못된 요청 (유효성 검사 실패)"),
        @ApiResponse(responseCode = "409", description = "이미 존재하는 정보 (이메일, 전화번호, 사업자등록번호 중복)")
    })
    public ResponseEntity<UserSignupResponse> signup(
        @Valid @RequestBody UserSignupRequest request) {
        log.info("회원가입 요청: {}", request.getEmail());

        UserSignupResponse response = userService.signup(request);

        log.info("회원가입 성공: {} (UUID: {})", response.getEmail(), response.getUserUuid());

        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    @GetMapping("/check-username")
    @Operation(summary = "사용자명 중복 확인", description = "사용자명 중복 여부를 확인합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "중복 확인 완료"),
        @ApiResponse(responseCode = "400", description = "잘못된 요청")
    })
    public ResponseEntity<Boolean> checkUserName(@RequestParam String userName) {
        log.info("사용자명 중복 확인 요청: {}", userName);

        boolean exists = userService.isUserNameExists(userName);

        return ResponseEntity.ok(exists);
    }

    @GetMapping("/check-userid")
    @Operation(summary = "사용자 ID 중복 확인", description = "사용자 ID 중복 여부를 확인합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "중복 확인 완료"),
        @ApiResponse(responseCode = "400", description = "잘못된 요청")
    })
    public ResponseEntity<Boolean> checkUserId(@RequestParam String userId) {
        log.info("사용자 ID 중복 확인 요청: {}", userId);

        boolean exists = userService.isUserIdExists(userId);

        return ResponseEntity.ok(exists);
    }

    @GetMapping("/by-role")
    @Operation(summary = "역할별 사용자 조회", description = "특정 역할의 사용자 목록을 조회합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "조회 완료"),
        @ApiResponse(responseCode = "400", description = "잘못된 요청")
    })
    public ResponseEntity<List<User>> getUsersByRole(@RequestParam UserRole role) {
        log.info("역할별 사용자 조회 요청: {}", role);

        List<User> users = userService.findUsersByRole(role);

        return ResponseEntity.ok(users);
    }

    @GetMapping("/count")
    @Operation(summary = "활성 사용자 수 조회", description = "현재 활성 상태인 사용자 수를 조회합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "조회 완료")
    })
    public ResponseEntity<Long> getActiveUserCount() {
        log.info("활성 사용자 수 조회 요청");

        long count = userService.getActiveUserCount();

        return ResponseEntity.ok(count);
    }

    @GetMapping("/{userId}")
    @Operation(summary = "사용자 ID로 조회", description = "사용자 ID로 사용자 정보를 조회합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "조회 완료"),
        @ApiResponse(responseCode = "404", description = "사용자를 찾을 수 없음")
    })
    public ResponseEntity<User> getUserByUserId(@PathVariable String userId) {
        log.info("사용자 ID로 조회 요청: {}", userId);

        User user = userService.findByUserId(userId);

        return ResponseEntity.ok(user);
    }

    @GetMapping("/name/{userName}")
    @Operation(summary = "사용자명으로 조회", description = "사용자명으로 사용자 정보를 조회합니다.")
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "조회 완료"),
        @ApiResponse(responseCode = "404", description = "사용자를 찾을 수 없음")
    })
    public ResponseEntity<User> getUserByUserName(@PathVariable String userName) {
        log.info("사용자명으로 조회 요청: {}", userName);

        User user = userService.findByUserName(userName);

        return ResponseEntity.ok(user);
    }
}
