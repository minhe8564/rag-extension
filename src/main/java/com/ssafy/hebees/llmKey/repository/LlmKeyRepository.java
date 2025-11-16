package com.ssafy.hebees.llmKey.repository;

import com.ssafy.hebees.llmKey.entity.LlmKey;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface LlmKeyRepository extends JpaRepository<LlmKey, UUID>, LlmKeyRepositoryCustom {
}
