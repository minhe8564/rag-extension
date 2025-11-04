package com.ssafy.hebees.dashboard.dto.response;

import java.util.List;

public record ErrorsTodayResponse(
    Timeframe timeframe,
    List<Error> errors
) {

    public record Error(
        String chatTitle,
        String userType,
        String userName,
        String chatRoomId,
        String errorType,
        String occuredAt
    ) {

    }
}
