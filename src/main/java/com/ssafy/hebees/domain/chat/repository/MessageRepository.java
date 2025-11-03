package com.ssafy.hebees.domain.chat.repository;

import com.ssafy.hebees.domain.chat.entity.Message;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.domain.Pageable;

public interface MessageRepository {

    Message save(Message message);

    List<Message> findBySessionNoOrderByCreatedAtAsc(UUID sessionNo);

    List<Message> findBySessionNoOrderBySeqDesc(UUID sessionNo, Pageable pageable);

    List<Message> findBySessionNoAndSeqLessThanOrderBySeqDesc(UUID sessionNo, Long seq,
        Pageable pageable);

    Optional<Message> findBySessionNoAndMessageNo(UUID sessionNo, UUID messageNo);
}

