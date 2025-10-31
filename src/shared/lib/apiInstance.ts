import axios, { AxiosError } from 'axios';
import type { InternalAxiosRequestConfig } from 'axios';
import { toast } from 'react-toastify';
import { useAuthStore } from '@/domains/auth/store/auth.store';

const BASE_URL = import.meta.env.VITE_API_BASE_URL;

const ERROR_MESSAGES: Record<string, string> = {
  BAD_REQUEST: '잘못된 요청입니다.',
  INVALID_INPUT: '필수 값이 누락되었습니다.',
  VALIDATION_FAILED: '입력값을 확인해주세요.',
  INVALID_LOGIN: '이메일 또는 비밀번호가 올바르지 않습니다.',
  INVALID_FILE_NAME: '허용되지 않은 파일 이름입니다.',
  INVALID_DATE_FORMAT: '날짜 형식이 올바르지 않습니다.',
  INVALID_DATE_RANGE: '날짜 범위가 올바르지 않습니다.',
  INVALID_TOKEN: '유효하지 않은 토큰입니다.',
  INVALID_ACCESS_TOKEN: '로그인이 만료되었습니다.',
  INVALID_REFRESH_TOKEN: '세션이 만료되었습니다. 다시 로그인해주세요.',
  FORBIDDEN: '접근 권한이 없습니다.',
  NOT_FOUND: '대상을 찾을 수 없습니다.',
  CONFLICT: '이미 존재하는 데이터입니다.',
  ALREADY_EXISTS_EMAIL: '이미 등록된 이메일입니다.',
  UNSUPPORTED_MEDIA_TYPE: '지원하지 않는 형식입니다.',
  INTERNAL_SERVER_ERROR: '서버 오류가 발생했습니다.',
  GATEWAY_TIMEOUT: '서버 응답이 지연되고 있습니다.',
};

const apiInstance = axios.create({
  baseURL: BASE_URL,
  withCredentials: true,
  timeout: 10000,
});

const refreshClient = axios.create({
  baseURL: BASE_URL,
  withCredentials: true,
  timeout: 10000,
});

function setAuthHeader(cfg: InternalAxiosRequestConfig, token: string) {
  if (!cfg.headers) cfg.headers = {} as any;
  const h: any = cfg.headers;
  if (typeof h.set === 'function') h.set('Authorization', `Bearer ${token}`);
  else h['Authorization'] = `Bearer ${token}`;
}

apiInstance.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const at = useAuthStore.getState().accessToken;
  if (at) setAuthHeader(config, at);
  return config;
});

let refreshPromise: Promise<string> | null = null;
const refreshAccessToken = () => {
  if (!refreshPromise) {
    refreshPromise = refreshClient
      .post('/api/v1/auth/refresh')
      .then(({ data }) => {
        const newAt = data?.result?.accessToken;
        if (!newAt) throw new Error('No accessToken in refresh result');
        useAuthStore.setState({ accessToken: newAt, isLoggedIn: true } as any);
        return newAt;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
};

apiInstance.interceptors.response.use(
  res => {
    const data = res.data;
    if (data && data.isSuccess === false) {
      const code: string | undefined = data.code;
      const msg =
        (code && ERROR_MESSAGES[code]) || data.message || '요청 처리 중 오류가 발생했습니다.';
      toast.error(msg);
      return Promise.reject(data);
    }
    return res;
  },
  async (error: AxiosError<any>) => {
    const { response, config } = error || {};
    const data = response?.data;
    const code: string | undefined = data?.code;
    const http = response?.status;
    const baseMsg = data?.message || response?.statusText || '잠시 후 다시 시도해주세요.';

    if (http === 401 && config && !(config as any)._retry) {
      try {
        (config as any)._retry = true;
        const newAt = await refreshAccessToken();
        setAuthHeader(config as InternalAxiosRequestConfig, newAt);
        return apiInstance.request(config!);
      } catch {
        toast.error(
          ERROR_MESSAGES[code || 'INVALID_REFRESH_TOKEN'] ||
            '세션이 만료되었습니다. 다시 로그인해주세요.'
        );
        useAuthStore.getState().logout?.();
        return Promise.reject(error);
      }
    }

    const msg = (code && ERROR_MESSAGES[code]) || baseMsg;

    switch (http) {
      case 400:
      case 403:
      case 404:
      case 409:
      case 415:
        toast.error(msg);
        break;
      case 500:
        toast.error(ERROR_MESSAGES.INTERNAL_SERVER_ERROR);
        break;
      case 504:
        toast.error(ERROR_MESSAGES.GATEWAY_TIMEOUT);
        break;
      default:
        toast.error(msg);
        console.error('[API ERROR]', error);
    }
    return Promise.reject(error);
  }
);

export default apiInstance;
