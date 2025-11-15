package com.ssafy.hebees.ragsetting.service;

import com.ssafy.hebees.common.dto.ListResponse;
import com.ssafy.hebees.common.exception.BusinessException;
import com.ssafy.hebees.common.exception.ErrorCode;
import com.ssafy.hebees.common.util.UserValidationUtil;
import com.ssafy.hebees.ragsetting.dto.request.LlmKeyCreateRequest;
import com.ssafy.hebees.ragsetting.dto.request.LlmKeySelfCreateRequest;
import com.ssafy.hebees.ragsetting.dto.request.LlmKeySelfUpdateRequest;
import com.ssafy.hebees.ragsetting.dto.request.LlmKeyUpdateRequest;
import com.ssafy.hebees.ragsetting.dto.response.LlmKeyResponse;
import com.ssafy.hebees.ragsetting.entity.LlmKey;
import com.ssafy.hebees.ragsetting.entity.Strategy;
import com.ssafy.hebees.ragsetting.repository.LlmKeyRepository;
import com.ssafy.hebees.ragsetting.repository.StrategyRepository;
import com.ssafy.hebees.user.entity.User;
import com.ssafy.hebees.user.repository.UserRepository;
import java.util.List;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

@Slf4j
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class LlmKeyServiceImpl implements LlmKeyService {

    private final LlmKeyRepository llmKeyRepository;
    private final UserRepository userRepository;
    private final StrategyRepository strategyRepository;

    @Override
    @Transactional
    public LlmKeyResponse create(LlmKeyCreateRequest request) {
        UUID userNo = request.userNo();
        UUID strategyNo = request.strategyNo();

        User user = fetchUser(userNo);
        Strategy strategy = fetchStrategy(strategyNo);

        ensureUniqueUserStrategy(user.getUuid(), strategy.getStrategyNo(), null);

        String apiKey = request.apiKey().trim();
        if (!StringUtils.hasText(apiKey)) {
            throw new BusinessException(ErrorCode.BAD_REQUEST);
        }

        LlmKey llmKey = LlmKey.builder()
            .user(user)
            .strategy(strategy)
            .apiKey(apiKey)
            .build();

        LlmKey saved = llmKeyRepository.save(llmKey);

        log.info("LLM Key 생성: llmKeyNo={}, userNo={}, strategyNo={}", saved.getLlmKeyNo(),
            userNo, strategyNo);

        return mapToResponse(saved);
    }

    @Override
    public LlmKeyResponse get(UUID llmKeyNo) {
        LlmKey llmKey = fetchLlmKey(llmKeyNo);
        return mapToResponse(llmKey);
    }

    @Override
    public ListResponse<LlmKeyResponse> list(UUID userNo) {
        List<LlmKey> keys = (userNo != null)
            ? llmKeyRepository.findAllByUser_Uuid(userNo)  // ← 여기만 수정
            : llmKeyRepository.findAll();

        return ListResponse.of(keys.stream().map(this::mapToResponse).toList());
    }


    @Override
    @Transactional
    public LlmKeyResponse update(UUID llmKeyNo, LlmKeyUpdateRequest request) {
        LlmKey llmKey = fetchLlmKey(llmKeyNo);

        boolean hasStrategyIdentifier = request.strategyNo() != null
            || StringUtils.hasText(request.llm());
        boolean hasApiKey = request.apiKey() != null;

        if (!hasStrategyIdentifier && !hasApiKey) {
            throw new BusinessException(ErrorCode.BAD_REQUEST);
        }

        if (hasStrategyIdentifier) {
            UUID strategyNo = request.strategyNo();
            if (strategyNo == null) {
                strategyNo = resolveStrategyNo(request.llm());
            }
            Strategy strategy = fetchStrategy(strategyNo);
            ensureUniqueUserStrategy(
                llmKey.getUser() != null ? llmKey.getUser().getUuid() : null,
                strategy.getStrategyNo(),
                llmKey.getLlmKeyNo()
            );
            llmKey.updateStrategy(strategy);
        }

        if (hasApiKey) {
            String apiKey = request.apiKey().trim();
            if (!StringUtils.hasText(apiKey)) {
                throw new BusinessException(ErrorCode.BAD_REQUEST);
            }
            llmKey.updateApiKey(apiKey);
        }

        LlmKey saved = llmKeyRepository.save(llmKey);

        log.info("LLM Key 수정: llmKeyNo={}, strategyChanged={}, apiKeyChanged={}", llmKeyNo,
            hasStrategyIdentifier, hasApiKey);

        return mapToResponse(saved);
    }

    @Override
    @Transactional
    public void delete(UUID llmKeyNo) {
        LlmKey llmKey = fetchLlmKey(llmKeyNo);
        llmKeyRepository.delete(llmKey);
        log.info("LLM Key 삭제: llmKeyNo={}", llmKeyNo);
    }

    @Override
    @Transactional
    public LlmKeyResponse createSelf(UUID userNo, LlmKeySelfCreateRequest request) {
        UUID owner = UserValidationUtil.requireUser(userNo);
        String identifier = request.llm();
        UUID strategyNo = resolveStrategyNo(identifier);
        Strategy strategy = fetchStrategy(strategyNo);

        String apiKey = request.apiKey().trim();
        if (!StringUtils.hasText(apiKey)) {
            throw new BusinessException(ErrorCode.BAD_REQUEST);
        }

        ensureUniqueUserStrategy(owner, strategy.getStrategyNo(), null);

        User user = fetchUser(owner);

        LlmKey saved = llmKeyRepository.save(
            LlmKey.builder()
                .user(user)
                .strategy(strategy)
                .apiKey(apiKey)
                .build()
        );

        log.info("LLM Key 생성(사용자): userNo={}, llmKeyNo={}", owner, saved.getLlmKeyNo());

        return mapToResponse(saved);
    }

    @Override
    public ListResponse<LlmKeyResponse> listSelf(UUID userNo) {
        UUID owner = UserValidationUtil.requireUser(userNo);
        return ListResponse.of(llmKeyRepository.findAllByUser_Uuid(owner).stream()
            .map(this::mapToResponse).toList());
    }

    @Override
    @Transactional
    public LlmKeyResponse updateSelf(UUID userNo, String llmIdentifier,
        LlmKeySelfUpdateRequest request) {
        UUID owner = UserValidationUtil.requireUser(userNo);
        LlmKey llmKey = fetchLlmKeyOwnedByUser(owner, llmIdentifier);

        boolean hasApiKey = request.apiKey() != null;

        if (!hasApiKey) {
            throw new BusinessException(ErrorCode.BAD_REQUEST);
        }

        if (hasApiKey) {
            String apiKey = request.apiKey().trim();
            if (!StringUtils.hasText(apiKey)) {
                throw new BusinessException(ErrorCode.BAD_REQUEST);
            }
            llmKey.updateApiKey(apiKey);
        }

        LlmKey saved = llmKeyRepository.save(llmKey);

        log.info("LLM Key 수정(사용자): userNo={}, llmIdentifier={}, apiKeyChanged={}",
            owner, llmIdentifier, hasApiKey);

        return mapToResponse(saved);
    }

    @Override
    @Transactional
    public void deleteSelf(UUID userNo, String llmIdentifier) {
        UUID owner = UserValidationUtil.requireUser(userNo);
        LlmKey llmKey = fetchLlmKeyOwnedByUser(owner, llmIdentifier);
        llmKeyRepository.delete(llmKey);
        log.info("LLM Key 삭제(사용자): userNo={}, llmIdentifier={}", owner, llmIdentifier);
    }

    @Override
    public LlmKeyResponse getSelfByLlm(UUID userNo, String llmIdentifier) {
        UUID owner = UserValidationUtil.requireUser(userNo);
        UUID strategyNo = resolveStrategyNo(llmIdentifier);
        LlmKey llmKey = llmKeyRepository.findByUser_UuidAndStrategy_StrategyNo(owner, strategyNo)
            .orElseThrow(() -> {
                log.warn("LLM Key 조회 실패 - 존재하지 않음: userNo={}, llmIdentifier={}", owner,
                    llmIdentifier);
                return new BusinessException(ErrorCode.NOT_FOUND);
            });
        return mapToResponse(llmKey);
    }

    private LlmKey fetchLlmKey(UUID llmKeyNo) {
        if (llmKeyNo == null) {
            throw new BusinessException(ErrorCode.INVALID_INPUT);
        }
        return llmKeyRepository.findById(llmKeyNo)
            .orElseThrow(() -> {
                log.warn("LLM Key 조회 실패 - 존재하지 않음: llmKeyNo={}", llmKeyNo);
                return new BusinessException(ErrorCode.NOT_FOUND);
            });
    }

    private LlmKey fetchLlmKeyOwnedByUser(UUID llmKeyNo, UUID userNo) {
        if (llmKeyNo == null) {
            throw new BusinessException(ErrorCode.INVALID_INPUT);
        }
        return llmKeyRepository.findByLlmKeyNoAndUser_Uuid(llmKeyNo, userNo)
            .orElseThrow(() -> {
                log.warn("LLM Key 조회 실패 - 소유자 불일치: llmKeyNo={}, userNo={}", llmKeyNo, userNo);
                return new BusinessException(ErrorCode.PERMISSION_DENIED);
            });
    }

    private LlmKey fetchLlmKeyOwnedByUser(UUID userNo, String llmIdentifier) {
        UUID strategyNo = resolveStrategyNo(llmIdentifier);
        return llmKeyRepository.findByUser_UuidAndStrategy_StrategyNo(userNo, strategyNo)
            .orElseThrow(() -> {
                log.warn("LLM Key 조회 실패 - 존재하지 않음: userNo={}, llmIdentifier={}", userNo,
                    llmIdentifier);
                return new BusinessException(ErrorCode.NOT_FOUND);
            });
    }

    private User fetchUser(UUID userNo) {
        if (userNo == null) {
            throw new BusinessException(ErrorCode.INVALID_INPUT);
        }
        return userRepository.findById(userNo)
            .orElseThrow(() -> {
                log.warn("사용자 조회 실패 - 존재하지 않음: userNo={}", userNo);
                return new BusinessException(ErrorCode.NOT_FOUND);
            });
    }

    private Strategy fetchStrategy(UUID strategyNo) {
        if (strategyNo == null) {
            throw new BusinessException(ErrorCode.INVALID_INPUT);
        }
        return strategyRepository.findByStrategyNo(strategyNo)
            .orElseThrow(() -> {
                log.warn("LLM 전략 조회 실패 - 존재하지 않음: strategyNo={}", strategyNo);
                return new BusinessException(ErrorCode.NOT_FOUND);
            });
    }

    private UUID resolveStrategyNo(String identifier) {
        String trimmed = identifier != null ? identifier.trim() : null;
        if (!StringUtils.hasText(trimmed)) {
            throw new BusinessException(ErrorCode.BAD_REQUEST);
        }

        try {
            UUID strategyNo = UUID.fromString(trimmed);
            return strategyRepository.findByStrategyNo(strategyNo)
                .map(Strategy::getStrategyNo)
                .orElseThrow(() -> new BusinessException(ErrorCode.BAD_REQUEST));
        } catch (IllegalArgumentException ignored) {
            return strategyRepository.findByNameAndCodeStartingWith(trimmed, "GEN")
                .orElseThrow(() -> new BusinessException(ErrorCode.BAD_REQUEST))
                .getStrategyNo();
        }
    }

    private void ensureUniqueUserStrategy(UUID userNo, UUID strategyNo, UUID excludeLlmKeyNo) {
        if (userNo == null || strategyNo == null) {
            throw new BusinessException(ErrorCode.INVALID_INPUT);
        }

        llmKeyRepository.findByUser_UuidAndStrategy_StrategyNo(userNo, strategyNo)
            .filter(existing -> excludeLlmKeyNo == null || !existing.getLlmKeyNo()
                .equals(excludeLlmKeyNo))
            .ifPresent(existing -> {
                log.warn(
                    "LLM Key 중복 - userNo={}, strategyNo={}, existingLlmKeyNo={}",
                    userNo, strategyNo, existing.getLlmKeyNo()
                );
                throw new BusinessException(ErrorCode.ALREADY_EXISTS);
            });
    }

    private LlmKeyResponse mapToResponse(LlmKey llmKey) {
        Strategy strategy = llmKey.getStrategy();
        String llmName = null;
        if (strategy != null) {
            if (StringUtils.hasText(strategy.getName())) {
                llmName = strategy.getName();
            } else if (StringUtils.hasText(strategy.getCode())) {
                llmName = strategy.getCode();
            }
        }

        return new LlmKeyResponse(
            llmKey.getLlmKeyNo(),
            llmKey.getUser() != null ? llmKey.getUser().getUuid() : null,
            strategy != null ? strategy.getStrategyNo() : null,
            strategy != null ? strategy.getStrategyNo() : null,
            llmName,
            llmKey.getApiKey()
        );
    }
}


