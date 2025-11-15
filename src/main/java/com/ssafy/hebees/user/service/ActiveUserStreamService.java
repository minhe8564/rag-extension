package com.ssafy.hebees.user.service;

import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

public interface ActiveUserStreamService {

    SseEmitter subscribeActiveUsers(String lastEventId);
}




