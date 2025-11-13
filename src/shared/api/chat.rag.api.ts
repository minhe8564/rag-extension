import { ragApi } from '@/shared/lib/apiInstance';
import type { ApiEnvelope } from '@/shared/lib/api.types';
import type { RagQueryProcessRequest, RagQueryProcessResult } from '@/shared/types/chat.rag.types';

export const postRagQuery = (payload: RagQueryProcessRequest) => {
  return ragApi.post<ApiEnvelope<RagQueryProcessResult>>('/query/process', payload);
};
