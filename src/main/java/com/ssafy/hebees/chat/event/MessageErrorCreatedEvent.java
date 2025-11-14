package com.ssafy.hebees.chat.event;

import com.ssafy.hebees.chat.entity.MessageErrorType;

public record MessageErrorCreatedEvent(MessageErrorType type) {

}

