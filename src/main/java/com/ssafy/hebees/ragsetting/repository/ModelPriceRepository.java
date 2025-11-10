package com.ssafy.hebees.ragsetting.repository;

import com.ssafy.hebees.ragsetting.entity.ModelPrice;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface ModelPriceRepository extends JpaRepository<ModelPrice, UUID> {

    Optional<ModelPrice> findByLlmNo(UUID llmNo);
}


