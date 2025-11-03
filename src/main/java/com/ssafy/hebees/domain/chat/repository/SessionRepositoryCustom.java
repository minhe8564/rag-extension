package com.ssafy.hebees.domain.chat.repository;

import com.ssafy.hebees.domain.chat.entity.Session;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;

import java.util.Optional;
import java.util.UUID;

public interface SessionRepositoryCustom {

    Optional<Session> findBySessionNo(UUID sessionNo);

    boolean existsByUserNoAndTitleIgnoreCase(UUID userNo, String title);

    Page<Session> searchSessionsByUser(UUID userNo, String keyword, Pageable pageable);
}


