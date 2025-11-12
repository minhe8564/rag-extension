package com.ssafy.hebees.chat.repository;

import com.ssafy.hebees.chat.entity.MessageError;
import java.util.UUID;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;

public interface MessageErrorRepositoryCustom {

    Page<MessageError> search(UUID sessionNo, UUID userNo, Pageable pageable);
}

