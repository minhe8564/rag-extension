import { springApi } from '@/shared/lib/apiInstance';
import type { ApiEnvelope } from '@/shared/lib/api.types';

export type Role = {
  uuid: string;
  mode: number;
  name: string;
};

// 역할 목록 조회
export const getRoles = async () => {
  const { data } = await springApi.get<ApiEnvelope<{ data: Role[] }>>('/api/v1/user/roles');
  return data.result?.data ?? [];
};

// 역할 상세 조회
export const getRoleById = async (userRoleNo: string) => {
  const { data } = await springApi.get<ApiEnvelope<Role>>(`/api/v1/user/roles/${userRoleNo}`);
  return data.result;
};

// 역할 생성
export const createRole = async (payload: { name: string; mode: number }) => {
  const { data } = await springApi.post<ApiEnvelope<Role>>('/api/v1/user/roles', payload);
  return data.result;
};

export const updateRole = async (userRoleNo: string, payload: Partial<Role>) => {
  await springApi.put<ApiEnvelope<unknown>>(`/api/v1/user/roles/${userRoleNo}`, payload);
};

// 역할 삭제
export const deleteRole = async (userRoleNo: string) => {
  await springApi.delete(`/api/v1/user/roles/${userRoleNo}`);
};
