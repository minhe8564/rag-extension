package com.ssafy.hebees.ragsetting.repository;

import com.ssafy.hebees.ragsetting.entity.Strategy;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface StrategyRepository extends JpaRepository<Strategy, UUID> {

    Optional<Strategy> findByStrategyNo(UUID strategyNo);
}
