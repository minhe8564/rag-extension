package com.ssafy.hebees.chat.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyList;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.ssafy.hebees.chat.client.RunpodClient;
import com.ssafy.hebees.chat.client.dto.RunpodChatMessage;
import com.ssafy.hebees.chat.client.dto.RunpodChatResult;
import com.ssafy.hebees.chat.dto.request.MessageCreateRequest;
import com.ssafy.hebees.chat.dto.response.AskResponse;
import com.ssafy.hebees.chat.dto.response.MessageResponse;
import com.ssafy.hebees.chat.entity.MessageRole;
import com.ssafy.hebees.chat.entity.Session;
import com.ssafy.hebees.chat.repository.SessionRepository;
import com.ssafy.hebees.common.exception.BusinessException;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
class ChatAskServiceImplTest {

    @Mock
    private SessionRepository sessionRepository;

    @Mock
    private MessageService messageService;

    @Mock
    private RunpodClient runpodClient;

    @InjectMocks
    private ChatAskServiceImpl chatAskService;

    private UUID userNo;
    private UUID sessionNo;
    private UUID llmNo;
    private Session session;
    private List<MessageResponse> history;

    @BeforeEach
    void setUp() {
        userNo = UUID.randomUUID();
        sessionNo = UUID.randomUUID();
        llmNo = UUID.randomUUID();

        session = Session.builder()
            .sessionNo(sessionNo)
            .title("test session")
            .userNo(userNo)
            .llmNo(llmNo)
            .lastRequestedAt(LocalDateTime.now())
            .build();

        history = new ArrayList<>();
        history.add(new MessageResponse(
            UUID.randomUUID(),
            MessageRole.SYSTEM,
            userNo,
            llmNo,
            "당신은 유능한 어시스턴트입니다.",
            LocalDateTime.now(),
            1L,
            List.of()
        ));
    }

    @Test
    void ask_success_returnsResponseAndPersistsMessages() {
        when(sessionRepository.findBySessionNo(sessionNo)).thenReturn(Optional.of(session));

        when(messageService.getAllMessages(userNo, sessionNo)).thenAnswer(
            invocation -> List.copyOf(history));

        when(messageService.createMessage(eq(userNo), eq(sessionNo),
            any(MessageCreateRequest.class)))
            .thenAnswer(invocation -> {
                MessageCreateRequest request = invocation.getArgument(2);
                MessageResponse response = new MessageResponse(
                    UUID.randomUUID(),
                    request.role(),
                    userNo,
                    llmNo,
                    request.content(),
                    LocalDateTime.now(),
                    (long) (history.size() + 1),
                    List.of()
                );
                history.add(response);
                return response;
            });

        RunpodChatResult runpodResult = new RunpodChatResult("assistant", "안녕하세요! 무엇을 도와드릴까요?");
        ArgumentCaptor<List<RunpodChatMessage>> captor = ArgumentCaptor.forClass(List.class);
        when(runpodClient.chat(anyList())).thenReturn(runpodResult);

        int expectedConversationSize = history.size() + 1; // 기존 이력 + 사용자 질문

        AskResponse response = chatAskService.ask(userNo, sessionNo, "첫 번째 질문입니다.");

        assertThat(response.content()).isEqualTo("안녕하세요! 무엇을 도와드릴까요?");
        assertThat(response.timestamp()).isNotNull();
        assertThat(history).hasSize(3); // system + human + ai
        assertThat(session.getLastRequestedAt()).isNotNull();

        verify(messageService, times(2)).createMessage(eq(userNo), eq(sessionNo),
            any(MessageCreateRequest.class));
        verify(runpodClient).chat(captor.capture());

        List<RunpodChatMessage> runpodMessages = captor.getValue();
        assertThat(runpodMessages).hasSize(expectedConversationSize);
        assertThat(runpodMessages.getLast().role()).isEqualTo("user");
    }

    @Test
    void ask_whenSessionNotOwned_throwsPermissionDenied() {
        Session otherSession = session.toBuilder()
            .userNo(UUID.randomUUID())
            .build();

        when(sessionRepository.findBySessionNo(sessionNo)).thenReturn(Optional.of(otherSession));

        assertThatThrownBy(() -> chatAskService.ask(userNo, sessionNo, "질문"))
            .isInstanceOf(BusinessException.class);
    }

    @Test
    void ask_whenQuestionBlank_throwsInvalidInput() {
        assertThatThrownBy(() -> chatAskService.ask(userNo, sessionNo, "   "))
            .isInstanceOf(BusinessException.class);
    }
}

