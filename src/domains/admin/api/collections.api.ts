import { fastApi } from '@/shared/lib/apiInstance';
import type { ApiEnvelope } from '@/shared/lib/api.types';
import type {
  collectionType,
  getDocumentsInCollection,
} from '@/domains/admin/types/documents.types';

// 컬렉션 목록 조회
export const getCollections = async () => {
  const { data } =
    await fastApi.get<ApiEnvelope<{ data: { data: collectionType[] } }>>('/api/v1/collections');
  return data.result;
};

// 컬렉션 내 문서 목록 조회
export const getDocInCollections = async (collectionNo: string) => {
  const { data } = await fastApi.get<ApiEnvelope<{ data: { data: getDocumentsInCollection } }>>(
    `/api/v1/collections/${collectionNo}/files`
  );
  return data.result;
};
