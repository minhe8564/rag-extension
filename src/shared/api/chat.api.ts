import { springApi } from '@/shared/lib/apiInstance';
import type { ApiEnvelope } from '@/shared/lib/api.types';
import type {
  SessionItem,
  ListSessionsParams,
  ListSessionsResult,
  ListMessagesParams,
  MessagePage,
  MessageItem,
  ReferencedDocument,
  SessionRequest,
  CreateSessionResult,
  SendMessageRequest,
  SendMessageResult,
} from '@/shared/types/chat.types';

// 세션 목록 조회
export function getSessions(params: ListSessionsParams = {}) {
  const { pageNum = 0, pageSize = 10, query } = params;

  return springApi.get<ApiEnvelope<ListSessionsResult>>('/api/v1/chat/sessions', {
    params: {
      pageNum,
      pageSize,
      ...(query ? { query } : {}),
    },
  });
}

// 세션 조회
export function getSession(sessionNo: string) {
  return springApi.get<ApiEnvelope<SessionItem>>(`/api/v1/chat/sessions/${sessionNo}`);
}

// 히스토리 조회
export function getMessages(sessionNo: string, params: ListMessagesParams = {}) {
  const { cursor, limit = 20 } = params;

  return springApi.get<ApiEnvelope<MessagePage>>(`/api/v1/chat/sessions/${sessionNo}/messages`, {
    params: {
      ...(cursor ? { cursor } : {}),
      limit,
    },
  });
}

// 메세지 조회
export function getMessage(sessionNo: string, messageNo: string) {
  return springApi.get<ApiEnvelope<MessageItem>>(
    `/api/v1/chat/sessions/${sessionNo}/history/${messageNo}`
  );
}

// 참조된 문서 조회
export function getReferencedDocuments(sessionNo: string, messageNo: string) {
  return springApi.get<ApiEnvelope<{ data: ReferencedDocument[] }>>(
    `/api/v1/chat/sessions/${sessionNo}/messages/${messageNo}/documents`
  );
}

// 세션 생성
export function createSession(body: SessionRequest = {}) {
  return springApi.post<ApiEnvelope<CreateSessionResult>>('/api/v1/chat/sessions', body);
}

// 세션 수정
export function updateSession(sessionNo: string, body: Partial<Pick<SessionItem, 'title'>>) {
  return springApi.put<ApiEnvelope<unknown>>(`/api/v1/chat/sessions/${sessionNo}`, body);
}

// 세션 삭제
export function deleteSession(sessionNo: string) {
  return springApi.delete<ApiEnvelope<unknown>>(`/api/v1/chat/sessions/${sessionNo}`);
}

// 메세지 전송
export function sendMessage(sessionNo: string, body: SendMessageRequest) {
  return springApi.post<ApiEnvelope<SendMessageResult>>(
    `/api/v1/chat/sessions/${sessionNo}/ask`,
    body
  );
}
