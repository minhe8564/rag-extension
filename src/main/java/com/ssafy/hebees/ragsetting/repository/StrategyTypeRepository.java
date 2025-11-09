package com.ssafy.hebees.ragsetting.repository;

import com.ssafy.hebees.ragsetting.entity.StrategyType;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface StrategyTypeRepository extends JpaRepository<StrategyType, UUID> {

    Optional<StrategyType> findByName(String name);
}
