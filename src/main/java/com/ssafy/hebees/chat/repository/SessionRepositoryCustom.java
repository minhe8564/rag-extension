package com.ssafy.hebees.chat.repository;

import com.ssafy.hebees.chat.entity.Session;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;

public interface SessionRepositoryCustom {

    Optional<Session> findBySessionNo(UUID sessionNo);

    boolean existsByUserNoAndTitleIgnoreCase(UUID userNo, String title);

    Page<Session> searchSessionsByUser(UUID userNo, String keyword, Pageable pageable);

    Page<Session> searchAllSessions(String keyword, Pageable pageable);

    List<Session> findCreatedBetween(LocalDateTime startInclusive, LocalDateTime endExclusive,
        int limit);
}


