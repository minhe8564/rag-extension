import api from '@/shared/lib/apiInstance';
import type { ApiEnvelope } from '@/shared/lib/api.types';

export type LoginResult = {
  accessToken: string;
  userNo: string;
  name: string;
  role: number;
};

export const login = async (email: string, password: string) => {
  const { data } = await api.post<ApiEnvelope<LoginResult>>('/api/v1/auth/login', {
    email,
    password,
  });
  return data.result;
};

export const logout = async () => {
  await api.post('/api/v1/auth/logout');
};
