import { fastApi } from '@/shared/lib/apiInstance';
import type { ApiEnvelope } from '@/shared/lib/api.types';
import type { collectionType } from '@/domains/admin/types/documents.types';

// 컬렉션 목록 조회
export const getCollections = async (params?: {
  pageNum?: number;
  pageSize?: number;
  filter?: boolean;
}) => {
  const { data } = await fastApi.get<ApiEnvelope<{ data: collectionType[]; pagination: any }>>(
    '/api/v1/collections',
    {
      params: {
        ...(params?.pageNum ? { pageNum: params.pageNum } : {}),
        ...(params?.pageSize ? { pageSize: params.pageSize } : {}),
        ...(params?.filter ? { filter: params.filter } : {}),
      },
    }
  );
  return data.result;
};

// 컬렉션 내 문서 목록 조회
export const getDocInCollections = async (
  collectionNo: string,
  params?: { pageNum?: number; pageSize?: number }
) => {
  const { data } = await fastApi.get(`/api/v1/collections/${collectionNo}/files`, {
    params: {
      ...(params?.pageNum ? { pageNum: params.pageNum } : {}),
      ...(params?.pageSize ? { pageSize: params.pageSize } : {}),
    },
  });
  return data.result;
};
