package com.ssafy.hebees.chat.client;

import com.ssafy.hebees.chat.client.dto.LlmChatRequest;
import com.ssafy.hebees.chat.client.dto.LlmChatResult;
import java.util.function.Consumer;

public interface StreamingLlmChatClient extends LlmChatClient {

    LlmChatResult stream(LlmChatRequest request, Consumer<String> onPartial);
}

