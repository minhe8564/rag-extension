import { fastApi } from '@/shared/lib/apiInstance';
import type { ApiEnvelope } from '@/shared/lib/api.types';
import type { Option } from '@/shared/components/Select';
import type {
  IngestTemplateListResult,
  IngestTemplateDetailResult,
  IngestTemplateListItem,
  UpsertIngestTemplateDto,
} from '@/domains/admin/types/rag-settings/templates.types';

// 목록
export async function getIngestTemplates(params?: {
  pageNum?: number;
  pageSize?: number;
}): Promise<IngestTemplateListResult> {
  const { pageNum = 1, pageSize = 20 } = params ?? {};
  const res = await fastApi.get<ApiEnvelope<IngestTemplateListResult>>(
    '/api/v1/rag/ingest-templates',
    { params: { pageNum, pageSize } }
  );
  return res.data.result;
}

// 상세
export async function getIngestTemplateDetail(
  ingestNo: string
): Promise<IngestTemplateDetailResult> {
  if (!ingestNo) throw new Error('ingestNo is required');
  const res = await fastApi.get<ApiEnvelope<IngestTemplateDetailResult>>(
    `/api/v1/rag/ingest-templates/${encodeURIComponent(ingestNo)}`
  );
  return res.data.result;
}

// 생성
export async function createIngestTemplate(
  payload: UpsertIngestTemplateDto
): Promise<IngestTemplateDetailResult> {
  const res = await fastApi.post<ApiEnvelope<IngestTemplateDetailResult>>(
    '/api/v1/rag/ingest-templates',
    payload
  );
  return res.data.result;
}

// 전체 수정(PUT)
export async function updateIngestTemplate(
  ingestNo: string,
  payload: UpsertIngestTemplateDto
): Promise<IngestTemplateDetailResult> {
  if (!ingestNo) throw new Error('ingestNo is required');
  const res = await fastApi.put<ApiEnvelope<IngestTemplateDetailResult>>(
    `/api/v1/rag/ingest-templates/${encodeURIComponent(ingestNo)}`,
    payload
  );
  return res.data.result;
}

// 부분 수정(PATCH)
export async function patchIngestTemplate(
  ingestNo: string,
  payload: Partial<UpsertIngestTemplateDto>
): Promise<IngestTemplateDetailResult> {
  if (!ingestNo) throw new Error('ingestNo is required');
  const res = await fastApi.patch<ApiEnvelope<IngestTemplateDetailResult>>(
    `/api/v1/rag/ingest-templates/${encodeURIComponent(ingestNo)}`,
    payload
  );
  return res.data.result;
}

// 삭제
export async function deleteIngestTemplate(ingestNo: string): Promise<null> {
  if (!ingestNo) throw new Error('ingestNo is required');
  const res = await fastApi.delete<ApiEnvelope<null>>(
    `/api/v1/rag/ingest-templates/${encodeURIComponent(ingestNo)}`
  );
  return res.data.result;
}

// Select 옵션 매핑
export function mapIngestTemplatesToOptions(list: IngestTemplateListItem[]): Option[] {
  return list.map((t) => ({
    value: t.ingestNo,
    label: t.name,
    desc: t.isDefault ? '기본 템플릿' : undefined,
  }));
}
