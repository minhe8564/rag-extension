package com.ssafy.hebees.dashboard.chat.service;

import com.ssafy.hebees.chat.entity.MessageError;
import com.ssafy.hebees.chat.entity.Session;
import com.ssafy.hebees.chat.repository.MessageErrorRepository;
import com.ssafy.hebees.chat.repository.SessionRepository;
import com.ssafy.hebees.dashboard.chat.dto.response.ChatroomsTodayResponse;
import com.ssafy.hebees.dashboard.chat.dto.response.ChatroomsTodayResponse.Chatroom;
import com.ssafy.hebees.dashboard.chat.dto.response.ErrorsTodayResponse;
import com.ssafy.hebees.dashboard.dto.response.Timeframe;
import com.ssafy.hebees.user.entity.User;
import com.ssafy.hebees.user.repository.UserRepository;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.UUID;
import java.util.function.Function;
import java.util.stream.Collectors;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class DashboardChatServiceImpl implements DashboardChatService {

    private static final int RECENT_CHATROOM_LIMIT = 100;
    private static final int RECENT_ERROR_LIMIT = 100;
    private static final String[] BUSINESS_TYPE_LABELS = {"개인 안경원", "체인 안경원", "제조 유통사"};

    private final SessionRepository sessionRepository;
    private final UserRepository userRepository;
    private final MessageErrorRepository messageErrorRepository;

    @Override
    public ChatroomsTodayResponse getChatroomsToday() {
        LocalDate today = LocalDate.now();
        LocalDateTime startInclusive = today.atStartOfDay();
        LocalDateTime endExclusive = startInclusive.plusDays(1);

        List<Session> sessions = sessionRepository.findCreatedBetween(
            startInclusive, endExclusive, RECENT_CHATROOM_LIMIT);

        if (sessions.isEmpty()) {
            return new ChatroomsTodayResponse(new Timeframe(today, today), List.of());
        }

        Set<UUID> userIds = sessions.stream()
            .map(Session::getUserNo)
            .filter(Objects::nonNull)
            .collect(Collectors.toSet());

        Map<UUID, User> usersById = userRepository.findAllById(userIds).stream()
            .collect(Collectors.toMap(User::getUuid, Function.identity()));

        List<Chatroom> chatrooms = sessions.stream()
            .sorted(Comparator.comparing(Session::getCreatedAt).reversed())
            .map(session -> {
                User owner = usersById.get(session.getUserNo());
                return new Chatroom(
                    session.getTitle(),
                    getUserType(owner),
                    owner != null ? owner.getName() : "-",
                    session.getSessionNo(),
                    session.getCreatedAt()
                );
            })
            .toList();

        return new ChatroomsTodayResponse(new Timeframe(today, today), chatrooms);
    }

    @Override
    public ErrorsTodayResponse getErrorsToday() {
        LocalDate today = LocalDate.now();
        LocalDateTime startInclusive = today.atStartOfDay();
        LocalDateTime endExclusive = startInclusive.plusDays(1);

        List<MessageError> errors = messageErrorRepository
            .findByCreatedAtBetweenOrderByCreatedAtDesc(
                startInclusive, endExclusive, RECENT_ERROR_LIMIT);

        if (errors.isEmpty()) {
            return new ErrorsTodayResponse(new Timeframe(today, today), List.of());
        }

        Set<UUID> sessionIds = errors.stream()
            .map(MessageError::getSessionNo)
            .filter(Objects::nonNull)
            .collect(Collectors.toSet());

        Map<UUID, Session> sessionsById = sessionRepository.findAllById(sessionIds).stream()
            .collect(Collectors.toMap(Session::getSessionNo, session -> session));

        Set<UUID> userIds = sessionsById.values().stream()
            .map(Session::getUserNo)
            .filter(Objects::nonNull)
            .collect(Collectors.toSet());

        Map<UUID, User> usersById = userRepository.findAllById(userIds).stream()
            .collect(Collectors.toMap(User::getUuid, user -> user));

        DateTimeFormatter formatter = DateTimeFormatter.ISO_LOCAL_DATE_TIME;

        List<ErrorsTodayResponse.Error> errorItems = errors.stream()
            .map(error -> {
                Session session = sessionsById.get(error.getSessionNo());
                User owner = session != null ? usersById.get(session.getUserNo()) : null;

                String chatTitle = session != null ? session.getTitle() : "알 수 없음";
                String userType = getUserType(owner);
                String userName = owner != null ? owner.getName() : "알 수 없음";
                String chatRoomId = session != null ? session.getSessionNo().toString()
                    : error.getSessionNo() != null ? error.getSessionNo().toString() : null;
                String errorType = error.getType() != null ? error.getType().name() : "UNKNOWN";
                String occurredAt = error.getCreatedAt() != null
                    ? error.getCreatedAt().format(formatter)
                    : null;

                return new ErrorsTodayResponse.Error(chatTitle, userType, userName, chatRoomId,
                    errorType, occurredAt);
            })
            .toList();

        return new ErrorsTodayResponse(new Timeframe(today, today), errorItems);
    }

    private String getUserType(User user) {
        if (user == null) {
            return "-";
        }

        int type = user.getBusinessType();
        if (0 <= type && type < BUSINESS_TYPE_LABELS.length) {
            return BUSINESS_TYPE_LABELS[type];
        }
        return "-";
    }
}


