package com.ssafy.hebees.llmKey.repository;

import com.ssafy.hebees.llmKey.entity.LlmKey;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface LlmKeyRepositoryCustom {

    List<LlmKey> findAllByUserUuid(UUID userNo);

    Optional<LlmKey> findByUserUuidAndStrategyNo(UUID userNo, UUID strategyNo);

    Optional<LlmKey> findSystemLlmKeyByStrategyNo(UUID strategyNo);
}
