import api from '@/shared/lib/apiInstance';
import type { ApiEnvelope } from '@/shared/lib/api.types';

type SignupPayload = {
  email: string;
  password: string;
  offerNo: string;
  businessType: number;
  name: string;
};

export const signup = async (payload: SignupPayload) => {
  const { data } = await api.post<ApiEnvelope<null>>('/api/v1/user/signup', payload);
  return data.result;
};
