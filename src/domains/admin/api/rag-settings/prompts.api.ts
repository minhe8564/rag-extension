import fastApi from '@/shared/lib/apiInstance';
import type { ApiEnvelope } from '@/shared/lib/api.types';
import type { Option } from '@/shared/components/Select';
import type {
  Prompt,
  PromptsListResult,
  PromptsListQuery,
  CreatePromptRequest,
  UpdatePromptRequest,
} from '@/domains/admin/types/rag-settings/prompts.types';

// 목록 조회
export async function getPrompts(params: PromptsListQuery = {}): Promise<PromptsListResult> {
  const { data } = await fastApi.get<ApiEnvelope<PromptsListResult>>('/api/v1/rag/prompts', {
    params,
  });
  return data.result;
}

// 상세 조회
export async function getPromptDetail(promptNo: string): Promise<Prompt> {
  const { data } = await fastApi.get<ApiEnvelope<Prompt>>(`/api/v1/rag/prompts/${promptNo}`);
  return data.result;
}

// 생성
export async function createPrompt(dto: CreatePromptRequest): Promise<string> {
  const { data } = await fastApi.post<ApiEnvelope<{ promptNo: string }>>('/api/rag/prompts', dto);
  return data.result.promptNo;
}

// 수정
export async function updatePrompt(promptNo: string, dto: UpdatePromptRequest): Promise<Prompt> {
  const { data } = await fastApi.put<ApiEnvelope<{ data: Prompt }>>(
    `/api/v1/rag/prompts/${promptNo}`,
    dto
  );
  return data.result.data;
}

// 삭제
export async function deletePrompt(promptNo: string): Promise<void> {
  await fastApi.delete(`/api/v1/rag/prompts/${promptNo}`);
}

export function mapPromptsToOptions(list: Prompt[]): Option[] {
  return list.map((p) => ({
    value: p.promptNo,
    label: p.name,
  }));
}
