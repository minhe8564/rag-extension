package com.ssafy.hebees.ragsetting.repository;

import com.ssafy.hebees.ragsetting.entity.LlmKey;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface LlmKeyRepository extends JpaRepository<LlmKey, UUID> {

    List<LlmKey> findAllByUser_Uuid(UUID userNo);

    Optional<LlmKey> findByLlmKeyNoAndUser_Uuid(UUID llmKeyNo, UUID userNo);

    Optional<LlmKey> findByUser_UuidAndStrategy_StrategyNo(UUID userNo, UUID strategyNo);

    Optional<LlmKey> findFirstByUserIsNullAndStrategy_StrategyNo(UUID strategyNo);
}


