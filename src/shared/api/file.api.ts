import { fastApi } from '@/shared/lib/apiInstance';
import type { ApiEnvelope } from '@/shared/lib/api.types';
import type {
  UploadFilesParams,
  UploadFilesResult,
  GetCategoriesResult,
  RawMyDoc,
  FilesResponse,
  FetchMyDocsNormalized,
  DeleteFileData,
} from '@/shared/types/file.types';

// 업로드
export function uploadFiles({
  files,
  categoryNo,
  bucket,
  onNameConflict = 'reject',
}: UploadFilesParams) {
  const form = new FormData();
  files.forEach((f) => form.append('files', f));
  form.append('category', categoryNo);
  if (bucket !== undefined && bucket !== null) form.append('bucket', bucket);

  return fastApi.post<ApiEnvelope<UploadFilesResult>>('/api/v1/files', form, {
    params: { onNameConflict },
  });
}

// 카테고리
export function getCategories() {
  return fastApi.get<ApiEnvelope<GetCategoriesResult>>('/api/v1/files/categories');
}

// 내 문서 목록(정규화)
export async function fetchMyDocumentsNormalized(params?: {
  pageNum?: number;
  pageSize?: number;
  categoryNo?: string;
  bucket?: string;
  q?: string;
}): Promise<FetchMyDocsNormalized> {
  const { data } = await fastApi.get<FilesResponse<RawMyDoc>>('/api/v1/files', {
    params: {
      pageNum: params?.pageNum ?? 1,
      pageSize: params?.pageSize ?? 20,
      ...(params ?? {}),
    },
  });

  const payload = data.result;
  const list = payload.data;
  const pg = payload.pagination;

  return {
    items: list.map((f) => ({
      fileNo: f.fileNo,
      name: f.name,
      sizeKB: f.size,
      type: f.type,
      bucket: f.bucket ?? undefined,
      path: f.path ?? undefined,
      status: f.status,
      categoryNo: f.categoryNo ?? undefined,
      collectionNo: f.collectionNo ?? undefined,
      createdAt: f.createdAt,
    })),
    total: pg.totalItems,
    totalPages: pg.totalPages,
    hasNext: pg.hasNext,
    pageNum: pg.pageNum,
    pageSize: pg.pageSize,
  };
}

// 파일 Presigned URL 발급
export async function getPresignedUrl(
  fileNo: string,
  opts?: { days?: number; inline?: boolean; contentType?: string; versionId?: string }
): Promise<string> {
  type PresignedUrlResponse = ApiEnvelope<{ data: { url: string } }>;

  const res = await fastApi.get<PresignedUrlResponse>(`/api/v1/files/${fileNo}/presigned`, {
    params: {
      ...(opts?.days !== undefined ? { days: opts.days } : {}),
      ...(opts?.inline !== undefined ? { inline: opts.inline } : {}),
      ...(opts?.contentType ? { contentType: opts.contentType } : {}),
      ...(opts?.versionId ? { versionId: opts.versionId } : {}),
    },
  });

  return res.data?.result?.data?.url;
}

// 파일 삭제
export async function deleteFile(fileNo: string): Promise<DeleteFileData> {
  const res = await fastApi.delete<ApiEnvelope<{ data: DeleteFileData }>>(
    `/api/v1/files/${fileNo}`
  );
  return res.data.result.data;
}
