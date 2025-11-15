package com.ssafy.hebees.chat.service;

import com.ssafy.hebees.chat.dto.request.MessageErrorCreateRequest;
import com.ssafy.hebees.chat.dto.request.MessageErrorSearchRequest;
import com.ssafy.hebees.chat.dto.response.MessageErrorCreateResponse;
import com.ssafy.hebees.chat.dto.response.MessageErrorResponse;
import com.ssafy.hebees.common.dto.PageRequest;
import com.ssafy.hebees.common.dto.PageResponse;
import java.util.UUID;

public interface MessageErrorService {

    MessageErrorCreateResponse createMessageError(UUID userNo,
        MessageErrorCreateRequest request);

    PageResponse<MessageErrorResponse> listMessageErrors(PageRequest pageRequest,
        MessageErrorSearchRequest searchRequest);

    void deleteMessageError(UUID errorMessageNo);
}

