import { springApi } from '@/shared/lib/apiInstance';
import type { ApiEnvelope } from '@/shared/lib/api.types';

export type LoginResult = {
  name: string;
  roleName: 'ADMIN' | 'USER';
  businessType: number;
  accessToken: string;
  refreshToken: string;
};

export const login = async (email: string, password: string) => {
  const { data } = await springApi.post<ApiEnvelope<LoginResult>>('/api/v1/auth/login', {
    email,
    password,
  });
  return data.result;
};

export const logout = async () => {
  await springApi.post('/api/v1/auth/logout');
};
