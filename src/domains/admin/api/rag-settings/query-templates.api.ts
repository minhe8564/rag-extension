import { fastApi } from '@/shared/lib/apiInstance';
import type { ApiEnvelope } from '@/shared/lib/api.types';
import type { Option } from '@/shared/components/Select';
import type {
  QueryTemplateListResult,
  QueryTemplateDetailResult,
  QueryTemplateListItem,
  UpsertQueryTemplateDto,
} from '@/domains/admin/types/rag-settings/templates.types';

// 목록
export async function getQueryTemplates(params?: {
  pageNum?: number;
  pageSize?: number;
}): Promise<QueryTemplateListResult> {
  const { pageNum = 1, pageSize = 20 } = params ?? {};
  const res = await fastApi.get<ApiEnvelope<QueryTemplateListResult>>(
    '/api/v1/rag/query-templates',
    { params: { pageNum, pageSize } }
  );
  return res.data.result;
}

// 상세
export async function getQueryTemplateDetail(queryNo: string): Promise<QueryTemplateDetailResult> {
  if (!queryNo) throw new Error('queryNo is required');
  const res = await fastApi.get<ApiEnvelope<QueryTemplateDetailResult>>(
    `/api/v1/rag/query-templates/${encodeURIComponent(queryNo)}`
  );
  return res.data.result;
}

// 생성
export async function createQueryTemplate(
  payload: UpsertQueryTemplateDto
): Promise<QueryTemplateDetailResult> {
  const res = await fastApi.post<ApiEnvelope<QueryTemplateDetailResult>>(
    '/api/v1/rag/query-templates',
    payload
  );
  return res.data.result;
}

// 수정
export async function putQueryTemplate(
  queryNo: string,
  payload: Partial<UpsertQueryTemplateDto>
): Promise<QueryTemplateDetailResult> {
  if (!queryNo) throw new Error('queryNo is required');
  const res = await fastApi.put<ApiEnvelope<QueryTemplateDetailResult>>(
    `/api/v1/rag/query-templates/${encodeURIComponent(queryNo)}`,
    payload
  );
  return res.data.result;
}

// 삭제
export async function deleteQueryTemplate(queryNo: string): Promise<null> {
  if (!queryNo) throw new Error('queryNo is required');
  const res = await fastApi.delete<ApiEnvelope<null>>(
    `/api/v1/rag/query-templates/${encodeURIComponent(queryNo)}`
  );
  return res.data.result;
}

// Select 옵션 매핑
export function mapQueryTemplatesToOptions(list: QueryTemplateListItem[]): Option[] {
  return list.map((t) => ({
    value: t.queryNo,
    label: t.name,
    desc: t.isDefault ? '기본 템플릿' : undefined,
  }));
}
