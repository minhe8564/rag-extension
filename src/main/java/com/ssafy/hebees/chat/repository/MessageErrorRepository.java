package com.ssafy.hebees.chat.repository;

import com.ssafy.hebees.chat.entity.MessageError;
import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface MessageErrorRepository extends JpaRepository<MessageError, UUID> {

    List<MessageError> findByCreatedAtBetweenOrderByCreatedAtDesc(LocalDateTime startInclusive,
        LocalDateTime endExclusive, Pageable pageable);
}


