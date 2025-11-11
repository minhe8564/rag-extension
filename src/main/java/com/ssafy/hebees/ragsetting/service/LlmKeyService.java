package com.ssafy.hebees.ragsetting.service;

import com.ssafy.hebees.ragsetting.dto.request.LlmKeyCreateRequest;
import com.ssafy.hebees.ragsetting.dto.request.LlmKeySelfCreateRequest;
import com.ssafy.hebees.ragsetting.dto.request.LlmKeyUpdateRequest;
import com.ssafy.hebees.ragsetting.dto.response.LlmKeyResponse;
import java.util.List;
import java.util.UUID;

public interface LlmKeyService {

    LlmKeyResponse create(LlmKeyCreateRequest request);

    LlmKeyResponse get(UUID llmKeyNo);

    List<LlmKeyResponse> list(UUID userNo);

    LlmKeyResponse update(UUID llmKeyNo, LlmKeyUpdateRequest request);

    void delete(UUID llmKeyNo);

    LlmKeyResponse createSelf(UUID userNo, LlmKeySelfCreateRequest request);

    List<LlmKeyResponse> listSelf(UUID userNo);

    LlmKeyResponse updateSelf(UUID userNo, UUID llmKeyNo, LlmKeyUpdateRequest request);

    void deleteSelf(UUID userNo, UUID llmKeyNo);

    LlmKeyResponse getSelfByLlm(UUID userNo, String llmIdentifier);
}


