import axios, { AxiosError } from 'axios';
import type { InternalAxiosRequestConfig, AxiosRequestConfig } from 'axios';
import { toast } from 'react-toastify';
import { useAuthStore } from '@/domains/auth/store/auth.store';

const BASE_URL = import.meta.env.VITE_API_BASE_URL;

const ERROR_MESSAGES: Record<string, string> = {
  BAD_REQUEST: '잘못된 요청입니다.',
  INVALID_INPUT: '필수 값이 누락되었습니다.',
  VALIDATION_FAILED: '입력값을 확인해주세요.',
  VALIDATION_ERROR: '입력값을 확인해주세요.',
  INVALID_SIGNIN: '이메일 또는 비밀번호가 올바르지 않습니다.',
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

function extractResultMessage(result: unknown): string | null {
  if (!result) return null;
  const flat = (v: any): string[] => {
    if (v == null) return [];
    if (typeof v === 'string') return [v];
    if (Array.isArray(v)) return v.flatMap(flat);
    if (typeof v === 'object') return Object.values(v).flatMap(flat);
    return [String(v)];
  };
  const lines = flat(result)
    .map(s => String(s).trim())
    .filter(Boolean);
  return lines.length ? lines.join('\n') : null;
}

function buildErrorMessage(payload: any): string {
  const code: string | undefined = payload?.code;
  const resultMsg = extractResultMessage(payload?.result);
  if (resultMsg) return resultMsg;
  if (code && ERROR_MESSAGES[code]) return ERROR_MESSAGES[code];
  if (payload?.message) return payload.message;
  return '요청 처리 중 오류가 발생했습니다.';
}

const REFRESH_EXCLUDE_CODES = new Set(['INVALID_SIGNIN', 'INVALID_CREDENTIALS']);

const REFRESH_EXCLUDE_PATHS = [
  /\/api\/v1\/auth\/login/i,
  /\/auth\/login/i,
  /\/login\b/i,
  /\/api\/v1\/auth\/refresh/i,
];

function isExcludedByUrl(url?: string) {
  if (!url) return false;
  return REFRESH_EXCLUDE_PATHS.some(re => re.test(url));
}

function canAttemptRefresh(http?: number, cfg?: AxiosRequestConfig, payload?: any): boolean {
  if (http !== 401) return false;
  const url = (cfg?.url || '') as string;
  if ((cfg as any)?._skipRefresh) return false;
  if (isExcludedByUrl(url)) return false;
  const code = payload?.code as string | undefined;
  if (code && REFRESH_EXCLUDE_CODES.has(code)) return false;
  return true;
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
      const msg = buildErrorMessage(data);
      toast.error(msg);
      return Promise.reject(data);
    }
    return res;
  },

  async (error: AxiosError<any>) => {
    const { response, config } = error || {};
    const payload = response?.data;
    const http = response?.status;

    if (canAttemptRefresh(http, config, payload) && config && !(config as any)._retry) {
      try {
        (config as any)._retry = true;
        const newAt = await refreshAccessToken();
        setAuthHeader(config as InternalAxiosRequestConfig, newAt);
        return apiInstance.request(config!);
      } catch {
        const code: string | undefined = payload?.code;
        const msg =
          ERROR_MESSAGES[code || 'INVALID_REFRESH_TOKEN'] ||
          '세션이 만료되었습니다. 다시 로그인해주세요.';
        toast.error(msg);
        useAuthStore.getState().logout?.();
        return Promise.reject(error);
      }
    }

    const fallback = payload?.message || response?.statusText || '잠시 후 다시 시도해주세요.';
    const msg = payload ? buildErrorMessage(payload) : fallback;

    switch (http) {
      case 400:
      case 401:
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
