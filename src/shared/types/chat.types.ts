import type { Pagination } from '@/shared/lib/api.types';

// 세션 목록 조회 관련
export interface SessionItem {
  sessionNo: string;
  title: string;
  createdAt?: string;
  lastRequestedAt?: string;
  updatedAt?: string;
  llmNo: string;
  llmName: string;
  userNo: string;
  userName: string;
}

export interface ListSessionsResult {
  data: SessionItem[];
  pagination: Pagination;
}

export interface ListSessionsParams {
  pageNum?: number;
  pageSize?: number;
  query?: string;
}

// 히스토리 조회 관련
export type ChatRole = 'human' | 'ai' | 'system' | 'tool';

export interface ReferencedDocument {
  fileNo: string;
  name: string;
  title?: string;
  type?: string;
  index: number;
  downloadUrl: string;
  snippet?: string;
}

export interface MessageItem {
  messageNo: string;
  role: ChatRole;
  content: string;
  createdAt: string;
  referencedDocuments?: ReferencedDocument[];
}

export interface MessagePage {
  data: MessageItem[];
  pagination: {
    hasNext: boolean;
    nextCursor: string;
    count: number;
  };
}

export interface ListMessagesParams {
  cursor?: string;
  limit?: number;
}

// 세션 생성 관련
export interface SessionRequest {
  title?: string;
  llm?: string;
  query?: string;
}

export interface CreateSessionResult {
  sessionNo: string;
  title?: string;
}

// 메세지 전송 관련
export interface SendMessageRequest {
  content: string;
  model?: string;
}

export interface SendMessageResult {
  content: string;
  createdAt: string;
  messageNo?: string;
}
