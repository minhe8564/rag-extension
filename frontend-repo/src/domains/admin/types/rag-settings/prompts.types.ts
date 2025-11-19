import type { Pagination } from '@/shared/lib/api.types';

export type PromptType = 'system' | 'user';

export interface Prompt {
  promptNo: string;
  name: string;
  type: PromptType;
  description?: string;
  content: string;
}

export interface PromptsListResult {
  data: Prompt[];
  pagination: Pagination;
}

export interface PromptsListQuery {
  pageNum?: number;
  pageSize?: number;
  type?: PromptType;
}

export interface CreatePromptRequest {
  name: string;
  type: PromptType;
  description: string;
  content: string;
}

export interface CreatePromptResult {
  promptNo: string;
}

export interface UpdatePromptRequest {
  name: string;
  type: PromptType;
  description: string;
  content: string;
}

export interface UpdatePromptResult {
  data: Prompt;
}
