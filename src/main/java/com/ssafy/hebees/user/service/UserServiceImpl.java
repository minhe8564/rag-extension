package com.ssafy.hebees.user.service;

import com.ssafy.hebees.common.exception.ErrorCode;
import com.ssafy.hebees.common.exception.BusinessException;
import com.ssafy.hebees.user.dto.UserSignupRequest;
import com.ssafy.hebees.user.dto.UserSignupResponse;
import com.ssafy.hebees.user.entity.User;
import com.ssafy.hebees.user.entity.UserRole;
import com.ssafy.hebees.user.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;

@Service
@RequiredArgsConstructor
@Slf4j
@Transactional(readOnly = true)
public class UserServiceImpl implements UserService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    @Override
    @Transactional
    public UserSignupResponse signup(UserSignupRequest request) {
        log.info("회원가입 시도: {}", request.getEmail());

        // 사용자명 중복 확인
        if (userRepository.existsByUserName(request.getName())) {
            throw new BusinessException(ErrorCode.ALREADY_EXISTS);
        }

        // 비밀번호 암호화
        String encodedPassword = passwordEncoder.encode(request.getPassword());

        // 사용자 ID 생성 (7자리 랜덤 문자열)
        String userId = generateUserId();

        // 사용자 엔티티 생성
        User user = User.builder()
            .userId(userId)
            .password(encodedPassword)
            .userName(request.getName())
            .role(request.getRole())
            .build();

        // 사용자 저장
        User savedUser = userRepository.save(user);
        log.info("회원가입 완료: {} (UUID: {})", savedUser.getUserName(), savedUser.getUuid());

        // 응답 DTO 생성
        return UserSignupResponse.builder()
            .userUuid(savedUser.getUuid())
            .email(request.getEmail()) // DTO에서 가져옴
            .name(savedUser.getUserName())
            .role(savedUser.getRole())
            .companyName(request.getCompanyName()) // DTO에서 가져옴
            .createdAt(savedUser.getCreatedAt())
            .build();
    }

    @Override
    public User findByUserId(String userId) {
        return userRepository.findByUserId(userId)
            .orElseThrow(() -> new BusinessException(ErrorCode.NOT_FOUND));
    }

    @Override
    public User findByUserName(String userName) {
        return userRepository.findByUserName(userName)
            .orElseThrow(() -> new BusinessException(ErrorCode.NOT_FOUND));
    }

    @Override
    public User findByUuid(UUID userUuid) {
        return userRepository.findById(userUuid)
            .orElseThrow(() -> new BusinessException(ErrorCode.NOT_FOUND));
    }

    @Override
    public boolean isUserNameExists(String userName) {
        return userRepository.existsByUserName(userName);
    }

    @Override
    public boolean isUserIdExists(String userId) {
        return userRepository.existsByUserId(userId);
    }

    @Override
    public List<User> findUsersByRole(UserRole role) {
        return userRepository.findByRole(role);
    }

    @Override
    public long getActiveUserCount() {
        return userRepository.countActiveUsers();
    }

    /**
     * 7자리 랜덤 사용자 ID 생성
     *
     * @return 생성된 사용자 ID
     */
    private String generateUserId() {
        String characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
        StringBuilder userId = new StringBuilder();

        for (int i = 0; i < 7; i++) {
            int index = (int) (Math.random() * characters.length());
            userId.append(characters.charAt(index));
        }

        // 중복 확인
        while (userRepository.existsByUserId(userId.toString())) {
            userId = new StringBuilder();
            for (int i = 0; i < 7; i++) {
                int index = (int) (Math.random() * characters.length());
                userId.append(characters.charAt(index));
            }
        }

        return userId.toString();
    }
}
