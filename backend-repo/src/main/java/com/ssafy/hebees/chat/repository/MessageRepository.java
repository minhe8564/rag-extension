package com.ssafy.hebees.chat.repository;

import com.ssafy.hebees.chat.entity.Message;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.bson.types.ObjectId;
import org.springframework.data.domain.Pageable;
import org.springframework.data.mongodb.repository.MongoRepository;

public interface MessageRepository extends MongoRepository<Message, ObjectId> {

    List<Message> findBySessionNoOrderByCreatedAtAsc(UUID sessionNo);

    List<Message> findBySessionNoOrderByCreatedAtDesc(UUID sessionNo, Pageable pageable);

    List<Message> findBySessionNoAndCreatedAtBeforeOrderByCreatedAtDesc(UUID sessionNo,
        LocalDateTime createdAt, Pageable pageable);

    Optional<Message> findBySessionNoAndMessageNo(UUID sessionNo, UUID messageNo);
}

