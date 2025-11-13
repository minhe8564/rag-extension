import type { ChatRole } from '@/shared/types/chat.types';

export type RagQueryProcessRequest = {
  llmNo: string;
  sessionNo: string;
  query: string;
};

export type RagQueryProcessResult = {
  messageNo: string;
  role: ChatRole;
  content: string;
  createdAt: string;
};
