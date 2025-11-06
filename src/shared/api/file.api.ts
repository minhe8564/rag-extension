import { fastApi } from '@/shared/lib/apiInstance';
import type { ApiEnvelope } from '@/shared/lib/api.types';
import type { GetCategoriesResult } from '@/shared/types/file.types';

// 카테고리 목록 조회
export function getCategories() {
  return fastApi.get<ApiEnvelope<GetCategoriesResult>>('/api/v1/files/categories');
}
