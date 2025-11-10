package com.ssafy.hebees.chat.service;

import com.ssafy.hebees.chat.dto.response.AskResponse;
import java.util.UUID;

public interface ChatAskService {

    AskResponse ask(UUID userNo, UUID sessionNo, String question);
}
