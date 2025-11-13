import { springApi } from '@/shared/lib/apiInstance';
import type { ApiEnvelope } from '@/shared/lib/api.types';

export type User = {
  userNo: string;
  email: string;
  name: string;
  role: number;
  offerNo: string;
  businessType: number;
};

export type Pagination = {
  pageNum: number;
  pageSize: number;
  totalItems: number;
  totalPages: number;
  hasNext: boolean;
};

export type UserListResponse = {
  data: User[];
  pagination: Pagination;
};

// 사용자 목록 조회
export const getUsers = async (
  params?: Partial<{
    pageNum: number;
    pageSize: number;
    role?: number;
    keyword?: string;
  }>
) => {
  const { data } = await springApi.get<ApiEnvelope<UserListResponse>>('/api/v1/user/users', {
    params,
  });
  return data.result;
};
