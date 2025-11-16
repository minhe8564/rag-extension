package com.ssafy.hebees.llmKey.service;

import com.ssafy.hebees.common.dto.ListResponse;
import com.ssafy.hebees.llmKey.dto.request.LlmKeyCreateRequest;
import com.ssafy.hebees.llmKey.dto.request.LlmKeyUpsertRequest;
import com.ssafy.hebees.llmKey.dto.response.LlmKeyResponse;
import java.util.UUID;

public interface LlmKeyService {

    ListResponse<LlmKeyResponse> listLlmKeys(UUID userNo);

    LlmKeyResponse getLlmKey(UUID userNo, String llmIdentifier);

    LlmKeyResponse createLlmKey(UUID userNo, LlmKeyCreateRequest request);

    LlmKeyResponse upsertLlmKey(UUID userNo, String llmIdentifier, LlmKeyUpsertRequest request);

    void deleteLlmKey(UUID userNo, String llmIdentifier);
}
