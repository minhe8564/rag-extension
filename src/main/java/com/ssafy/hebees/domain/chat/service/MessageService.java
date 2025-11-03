package com.ssafy.hebees.domain.chat.service;

import com.ssafy.hebees.domain.chat.dto.request.MessageCreateRequest;
import com.ssafy.hebees.domain.chat.dto.request.MessageCursorRequest;
import com.ssafy.hebees.domain.chat.dto.response.MessageCursorResponse;
import com.ssafy.hebees.domain.chat.dto.response.MessageResponse;
import com.ssafy.hebees.domain.chat.dto.response.ReferencedDocumentListResponse;
import com.ssafy.hebees.domain.chat.dto.response.ReferencedDocumentResponse;
import java.util.UUID;

public interface MessageService {

    MessageResponse createMessage(UUID userNo, UUID sessionNo, MessageCreateRequest request);

    MessageCursorResponse listMessages(UUID userNo, UUID sessionNo, MessageCursorRequest request);

    MessageResponse getMessage(UUID userNo, UUID sessionNo, UUID messageNo);

    ReferencedDocumentListResponse listReferencedDocuments(UUID userNo, UUID sessionNo,
        UUID messageNo);

    ReferencedDocumentResponse getReferencedDocument(UUID userNo, UUID sessionNo, UUID messageNo,
        UUID documentNo);
}

