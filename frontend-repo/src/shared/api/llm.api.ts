import { springApi } from '@/shared/lib/apiInstance';
import type { ApiEnvelope } from '@/shared/lib/api.types';
import type {
  MyLlmKeyCreateRequest,
  MyLlmKeyResponse,
  MyLlmKeyListResponse,
} from '@/shared/types/llm.types';

// 내 LLM Key 목록 조회
export const getMyLlmKeys = () =>
  springApi.get<ApiEnvelope<MyLlmKeyListResponse>>('/api/v1/rag-settings/llm-keys/me');

// 내 LLM Key 생성
export const createMyLlmKey = (data: MyLlmKeyCreateRequest) =>
  springApi.post<ApiEnvelope<MyLlmKeyResponse>>('/api/v1/rag-settings/llm-keys/me', data);

// 내 LLM Key 단건 조회
export const getMyLlmKeyByName = (llmName: string) =>
  springApi.get<ApiEnvelope<MyLlmKeyResponse>>(`/api/v1/rag-settings/llm-keys/me/${llmName}`);

// 내 LLM Key 수정
export const updateMyLlmKey = (llmNo: string, data: Partial<MyLlmKeyCreateRequest>) =>
  springApi.put<ApiEnvelope<MyLlmKeyResponse>>(`/api/v1/rag-settings/llm-keys/me/${llmNo}`, data);

// 내 LLM Key 삭제
export const deleteMyLlmKey = (llmNo: string) =>
  springApi.delete(`/api/v1/rag-settings/llm-keys/me/${llmNo}`);
