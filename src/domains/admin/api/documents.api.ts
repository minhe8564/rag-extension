import { springApi } from '@/shared/lib/apiInstance';
import type { ApiEnvelope } from '@/shared/lib/api.types';
import type {
  CollectionList,
  getDocumentsInCollection,
} from '@/domains/admin/types/documents.types';

// 컬렉션 목록 조회
export const getCollections = async (params: {
  pageNum?: number;
  pageSize?: number;
  env?: string;
}) => {
  const { data } = await springApi.get<ApiEnvelope<CollectionList>>('/collections', {
    params,
  });
  return data.result;
};

// 컬렉션 내 문서 목록 조회
export const getDocInCollections = async (
  collectionNo: string,
  params: { pageNum: number; pageSize: number }
) => {
  const { data } = await springApi.get<ApiEnvelope<getDocumentsInCollection>>(
    `/collections/${collectionNo}/documents`,
    {
      params,
    }
  );
  return data.result;
};
