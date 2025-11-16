package com.ssafy.hebees.llmKey.service;

import com.ssafy.hebees.common.dto.ListResponse;
import com.ssafy.hebees.common.exception.BusinessException;
import com.ssafy.hebees.common.exception.ErrorCode;
import com.ssafy.hebees.common.util.ValidationUtil;
import com.ssafy.hebees.llmKey.dto.request.LlmKeyCreateRequest;
import com.ssafy.hebees.llmKey.dto.request.LlmKeyUpsertRequest;
import com.ssafy.hebees.llmKey.dto.response.LlmKeyResponse;
import com.ssafy.hebees.llmKey.entity.LlmKey;
import com.ssafy.hebees.ragsetting.entity.Strategy;
import com.ssafy.hebees.llmKey.repository.LlmKeyRepository;
import com.ssafy.hebees.ragsetting.repository.StrategyRepository;
import com.ssafy.hebees.user.entity.User;
import com.ssafy.hebees.user.repository.UserRepository;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Slf4j
@Service
@RequiredArgsConstructor
@Transactional
public class LlmKeyServiceImpl implements LlmKeyService {

    private final LlmKeyRepository llmKeyRepository;
    private final UserRepository userRepository;
    private final StrategyRepository strategyRepository;
    private final LlmKeyCacheService llmKeyCacheService;


    @Override
    @Transactional(readOnly = true)
    public ListResponse<LlmKeyResponse> listLlmKeys(UUID userNo) {
        ValidationUtil.require(userNo);

        List<LlmKey> keys = llmKeyRepository.findAllByUserUuid(userNo);
        List<Strategy> strategies = strategyRepository.findByCodeStartingWith("GEN");
        Map<UUID, Strategy> strategyMap = new HashMap<>();
        strategies.forEach(strategy -> strategyMap.put(strategy.getStrategyNo(), strategy));

        List<LlmKeyResponse> list = keys.stream().map(
            llmKey -> {
                Strategy llm = strategyMap.get(llmKey.getStrategy().getStrategyNo());
                UUID llmNo = llm != null ? llm.getStrategyNo() : null;
                String llmName = llm != null ? llm.getName() : null;

                return LlmKeyResponse.builder()
                    .hasKey(true)
                    .llmKeyNo(llmKey.getLlmKeyNo())
                    .userNo(userNo)
                    .strategyNo(llmNo)
                    .llmNo(llmNo)
                    .llmName(llmName)
                    .apiKey(llmKey.getApiKey())
                    .build();
            }).toList();

        return ListResponse.of(list);
    }

    @Override
    @Transactional(readOnly = true)
    public LlmKeyResponse getLlmKey(UUID userNo, String llmIdentifier) {
        ValidationUtil.require(userNo);
        UUID llmNo = llmKeyCacheService.fetchLlmNo(llmIdentifier);

        return llmKeyRepository.findByUserUuidAndStrategyNo(userNo, llmNo)
            .map(this::toResponse)
            .orElseGet(() -> LlmKeyResponse.builder().hasKey(false).build());
    }

    @Override
    public LlmKeyResponse createLlmKey(UUID userNo, LlmKeyCreateRequest request) {
        ValidationUtil.require(userNo);
        UUID llmNo = llmKeyCacheService.fetchLlmNo(request.llm());
        String apiKey = ValidationUtil.require(request.apiKey());

        ensureUniqueUserStrategy(userNo, llmNo);

        Strategy llm = strategyRepository.findById(llmNo)
            .orElseThrow(() -> {
                log.warn("LLM 조회 실패 - 존재하지 않음: llmNo={}", llmNo);
                return new BusinessException(ErrorCode.NOT_FOUND);
            });
        User user = userRepository.getReferenceById(userNo);

        LlmKey saved = llmKeyRepository.save(
            LlmKey.builder()
                .user(user)
                .strategy(llm)
                .apiKey(apiKey)
                .build()
        );

        log.info("LLM Key 생성: userNo={}, llmNo={}, llmKeyNo={}", userNo, llm.getStrategyNo(),
            saved.getLlmKeyNo());

        return toResponse(saved);
    }

    @Override
    public LlmKeyResponse upsertLlmKey(UUID userNo, String llmIdentifier,
        LlmKeyUpsertRequest request) {
        ValidationUtil.require(userNo);
        UUID llmNo = llmKeyCacheService.fetchLlmNo(llmIdentifier);
        String apiKey = ValidationUtil.require(request.apiKey());

        LlmKey llmKey = llmKeyRepository.findByUserUuidAndStrategyNo(userNo, llmNo)
            .orElseGet(() -> {
                User userRef = userRepository.getReferenceById(userNo);
                Strategy llmRef = strategyRepository.getReferenceById(llmNo);

                log.info("LLM Key가 없으므로 생성합니다: userNo={}, llmNo={}", userNo, llmNo);
                return LlmKey.builder()
                    .user(userRef)
                    .strategy(llmRef)
                    .build();
            });

        llmKey.updateApiKey(apiKey);

        LlmKey saved = llmKeyRepository.save(llmKey);

        log.info("LLM Key 수정: userNo={}, llmIdentifier={}", userNo, llmIdentifier);

        return toResponse(saved);
    }

    @Override
    public void deleteLlmKey(UUID userNo, String llmIdentifier) {
        ValidationUtil.require(userNo);
        UUID llmNo = llmKeyCacheService.fetchLlmNo(llmIdentifier);

        LlmKey llmKey = llmKeyRepository.findByUserUuidAndStrategyNo(userNo, llmNo)
            .orElseThrow(() -> {
                log.warn("LLM Key 조회 실패 - 존재하지 않음: userNo={}, llmIdentifier={}",
                    userNo, llmIdentifier);
                return new BusinessException(ErrorCode.NOT_FOUND);
            });

        llmKeyRepository.delete(llmKey);

        log.info("LLM Key 삭제: userNo={}, llmIdentifier={}", userNo, llmIdentifier);
    }

    private void ensureUniqueUserStrategy(UUID userNo, UUID llmNo) {
        llmKeyRepository.findByUserUuidAndStrategyNo(userNo, llmNo)
            .ifPresent(existing -> {
                log.warn("LLM Key 중복 - userNo={}, llmNo={}, existingLlmKeyNo={}",
                    userNo, llmNo, existing.getLlmKeyNo()
                );
                throw new BusinessException(ErrorCode.ALREADY_EXISTS);
            });
    }

    private LlmKeyResponse toResponse(LlmKey llmKey) {
        Strategy llm = llmKey.getStrategy() != null ? llmKey.getStrategy() : null;
        UUID llmNo = llm != null ? llm.getStrategyNo() : null;
        String llmName = llm != null ? llm.getName() : null;

        return LlmKeyResponse.builder()
            .hasKey(true)
            .llmKeyNo(llmKey.getLlmKeyNo())
            .userNo(llmKey.getUser() != null ? llmKey.getUser().getUuid() : null)
            .strategyNo(llmNo)
            .llmNo(llmNo)
            .llmName(llmName)
            .apiKey(llmKey.getApiKey())
            .build();
    }
}
