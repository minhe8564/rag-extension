package com.ssafy.hebees.user.service;

import com.ssafy.hebees.common.exception.BusinessException;
import com.ssafy.hebees.common.exception.ErrorCode;
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
        // 회원가입 비즈니스 로직: 이메일/이름 중복 확인 → OFFER 검증/생성 → USER 권한 부여 → 저장
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

        String offerNo = request.offerNo();

        // 입력받은 offerNo로 기존 OFFER 존재 여부 확인. 없으면 신규 OFFER 생성 후 진행
        Offer offer = offerRepository.findByBusinessNoWithQueryDSL(offerNo)
            .orElseGet(() -> {
                log.info("신규 OFFER 생성: {}", offerNo);
                return offerRepository.save(Offer.builder()
                    .offerNo(offerNo)
                    .version(1)
                    .build());
            });

        // 기본 권한(USER)이 없으면 최초 1회 생성
        UserRole userRole = userRoleRepository.findByNameWithQueryDSL("USER")
            .orElseGet(() -> {
                log.info("신규 UserRole 생성: USER");
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
            .orElseThrow(() -> new BusinessException(ErrorCode.INVALID_SIGNIN));
    }

    @Override
    public User findByName(String name) {
        return userRepository.findByNameWithQueryDSL(name)
            .orElseThrow(() -> new BusinessException(ErrorCode.INVALID_SIGNIN));
    }

    @Override
    public User findByUuid(UUID userUuid) {
        return userRepository.findById(userUuid)
            .orElseThrow(() -> new BusinessException(ErrorCode.INVALID_SIGNIN));
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

