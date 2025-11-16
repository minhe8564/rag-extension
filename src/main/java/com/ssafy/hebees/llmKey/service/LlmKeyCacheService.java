package com.ssafy.hebees.llmKey.service;

import com.ssafy.hebees.common.exception.BusinessException;
import com.ssafy.hebees.common.exception.ErrorCode;
import com.ssafy.hebees.common.util.ValidationUtil;
import com.ssafy.hebees.ragsetting.repository.StrategyRepository;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class LlmKeyCacheService {

    private final StrategyRepository strategyRepository;

    @Cacheable(cacheNames = "cache:llmNo", key = "#llmIdentifier")
    public UUID fetchLlmNo(String llmIdentifier) {
        llmIdentifier = ValidationUtil.require(llmIdentifier);

        try { // UUID 라면 바로 반환
            return UUID.fromString(llmIdentifier);
        } catch (IllegalArgumentException ignored) { // 이름이면 UUID로 변환
            return strategyRepository.findByNameAndCodeStartingWith(llmIdentifier, "GEN")
                .orElseThrow(() -> new BusinessException(ErrorCode.BAD_REQUEST))
                .getStrategyNo();
        }
    }
}
