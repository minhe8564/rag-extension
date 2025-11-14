package com.ssafy.hebees.chat.client;

import com.ssafy.hebees.chat.client.dto.LlmChatRequest;
import com.ssafy.hebees.chat.client.dto.LlmChatResult;

public interface LlmChatClient {

    boolean supports(LlmProvider provider);

    LlmChatResult chat(LlmChatRequest request);
}

