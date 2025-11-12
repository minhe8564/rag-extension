package com.ssafy.hebees.chat.event;

import java.util.UUID;

public record SessionTitleGenerationEvent(UUID sessionNo, String query) {

}

