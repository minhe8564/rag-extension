import { fastApi } from '@/shared/lib/apiInstance';
import type { ApiEnvelope } from '@/shared/lib/api.types';
import type {
  UploadFilesParams,
  UploadFilesResult,
  GetCategoriesResult,
  RawMyDoc,
  FilesResponse,
  FetchMyDocsNormalized,
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

  return fastApi.post<UploadFilesResult>('/api/v1/files', form, { params: { onNameConflict } });
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

  const payload = data.result.data;
  const list = payload.data;
  const pg = payload.pagination;

  return {
    items: list.map((f) => ({
      fileNo: f.fileNo,
      name: f.name,
      sizeKB: f.size,
      type: f.type,
      bucket: f.bucket,
      path: f.path,
      categoryNo: f.categoryNo,
      collectionNo: f.collectionNo,
      uploadedAt: f.createdAt,
    })),
    total: pg.totalItems,
    totalPages: pg.totalPages,
    hasNext: pg.hasNext,
    pageNum: pg.pageNum,
    pageSize: pg.pageSize,
  };
}

// 문서 삭제
export const deleteDocument = async (fileNo: string) => {
  const { data } = await fastApi.delete(`/api/v1/files/${fileNo}`);
  return data.result;
};
