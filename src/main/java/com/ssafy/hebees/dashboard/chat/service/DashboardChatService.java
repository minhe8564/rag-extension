package com.ssafy.hebees.dashboard.chat.service;

import com.ssafy.hebees.dashboard.chat.dto.response.ChatroomsTodayResponse;
import com.ssafy.hebees.dashboard.chat.dto.response.ErrorsTodayResponse;

public interface DashboardChatService {

    ChatroomsTodayResponse getChatroomsToday();

    ErrorsTodayResponse getErrorsToday();
}


