package com.ssafy.hebees.dashboard.chat.dto.response;

import com.ssafy.hebees.dashboard.dto.response.Timeframe;
import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

public record ChatroomsTodayResponse(
    Timeframe timeframe,
    List<Chatroom> chatrooms
) {

    public static ChatroomsTodayResponse empty(Timeframe timeframe) {
        return new ChatroomsTodayResponse(timeframe, List.of());
    }

    public record Chatroom(
        String title,
        String userType,
        String userName,
        UUID chatRoomId,
        LocalDateTime createdAt
    ) {

    }
}