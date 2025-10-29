package com.ssafy.hebees.user.service;

import com.ssafy.hebees.common.exception.ErrorCode;
import com.ssafy.hebees.common.exception.BusinessException;
import com.ssafy.hebees.offer.entity.Offer;
import com.ssafy.hebees.offer.repository.OfferRepository;
import com.ssafy.hebees.user.dto.request.UserSignupRequest;
import com.ssafy.hebees.user.dto.response.UserSignupResponse;
import com.ssafy.hebees.user.entity.User;
import com.ssafy.hebees.user.entity.UserRole;
import com.ssafy.hebees.user.repository.UserRepository;
import com.ssafy.hebees.user.repository.UserRoleRepository;
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
    private final OfferRepository offerRepository;
    private final UserRoleRepository userRoleRepository;
    private final PasswordEncoder passwordEncoder;

    @Override
    @Transactional
    public UserSignupResponse signup(UserSignupRequest request) {
        log.info("회원가입 시도: {}", request.email());

        // 이메일 중복 확인
        if (userRepository.findByEmailWithQueryDSL(request.email()).isPresent()) {
            throw new BusinessException(ErrorCode.ALREADY_EXISTS);
        }

        // 사용자명 중복 확인
        if (userRepository.findByNameWithQueryDSL(request.name()).isPresent()) {
            throw new BusinessException(ErrorCode.ALREADY_EXISTS);
        }

        // 비밀번호 암호화
        String encodedPassword = passwordEncoder.encode(request.password());

        String businessNo = request.businessNumber().replace("-", "");

        Offer offer = offerRepository.findByBusinessNoWithQueryDSL(businessNo)
            .orElseGet(() -> {
                log.info("새로운 사업자 번호로 Offer 생성: {} (원본: {})", businessNo, request.businessNumber());
                return offerRepository.save(Offer.builder()
                    .offerNo(businessNo) // 하이픈 제거된 사업자 번호로 저장
                    .version(1)
                    .build());
            });

        UserRole userRole = userRoleRepository.findByNameWithQueryDSL("USER")
            .orElseGet(() -> {
                log.info("새로운 UserRole 생성: USER");
                return userRoleRepository.save(UserRole.builder()
                    .name("USER")
                    .mode(1)
                    .build());
            });

        // 사용자 엔티티 생성
        User user = User.builder()
            .email(request.email())
            .password(encodedPassword)
            .name(request.name())
            .userRole(userRole)
            .offer(offer)
            .businessType(request.businessType())
            .build();

        // 사용자 저장
        User savedUser = userRepository.save(user);
        log.info("회원가입 완료: {} (UUID: {})", savedUser.getName(), savedUser.getUuid());

        // 응답 DTO 생성
        return UserSignupResponse.of(savedUser);
    }

    @Override
    public User findByEmail(String email) {
        return userRepository.findByEmailWithQueryDSL(email)
            .orElseThrow(() -> new BusinessException(ErrorCode.NOT_FOUND));
    }

    @Override
    public User findByName(String name) {
        return userRepository.findByNameWithQueryDSL(name)
            .orElseThrow(() -> new BusinessException(ErrorCode.NOT_FOUND));
    }

    @Override
    public User findByUuid(UUID userUuid) {
        return userRepository.findById(userUuid)
            .orElseThrow(() -> new BusinessException(ErrorCode.NOT_FOUND));
    }

    @Override
    public boolean isNameExists(String name) {
        return userRepository.findByNameWithQueryDSL(name).isPresent();
    }

    @Override
    public boolean isEmailExists(String email) {
        return userRepository.findByEmailWithQueryDSL(email).isPresent();
    }

    @Override
    public List<User> findUsersByRoleName(String roleName) {
        return userRepository.findByRoleName(roleName);
    }

    @Override
    public long getActiveUserCount() {
        return userRepository.countActiveUsers();
    }
}
