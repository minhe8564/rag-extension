import axios, { AxiosError } from 'axios';
import type { InternalAxiosRequestConfig } from 'axios';
import { toast } from 'react-toastify';
import { useAuthStore } from '@/domains/auth/store/auth.store';

// Axios config 타입 확장 추가
interface RetryAxiosRequestConfig extends InternalAxiosRequestConfig {
  _retry?: boolean;
}

// 환경변수 정리
const SPRING_API_BASE_URL = import.meta.env.VITE_SPRING_BASE_URL;
const RAG_API_BASE_URL = import.meta.env.VITE_RAG_BASE_URL;
const FASTAPI_BASE_URL = import.meta.env.VITE_FASTAPI_BASE_URL;

// 인스턴스 생성
export const springApi = axios.create({
  baseURL: SPRING_API_BASE_URL,
  withCredentials: true,
  timeout: 180000,
});

export const ragApi = axios.create({
  baseURL: RAG_API_BASE_URL,
  withCredentials: true,
  timeout: 180000,
});

export const fastApi = axios.create({
  baseURL: FASTAPI_BASE_URL,
  withCredentials: true,
  timeout: 180000,
});

// 에러 코드별 메세지 정의
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

// refresh 제외 URL
const REFRESH_EXCLUDE = [/\/auth\/login/i, /\/auth\/refresh/i];

function shouldExcludeFromRefresh(url?: string): boolean {
  if (!url) return false;
  return REFRESH_EXCLUDE.some((re) => re.test(url));
}

function isRefreshUrl(url?: string): boolean {
  return !!url && /\/api\/v1\/auth\/refresh(?:$|\?)/i.test(url);
}

// token setter
function setAuthHeader(config: InternalAxiosRequestConfig, token: string) {
  config.headers = config.headers ?? {};
  config.headers.Authorization = `Bearer ${token}`;
}

// refresh promise
let refreshPromise: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  if (!refreshPromise) {
    refreshPromise = springApi
      .post('/api/v1/auth/refresh', undefined, { withCredentials: true })
      .then((res) => {
        const newToken = res?.data?.result?.accessToken;
        if (!newToken) throw new Error('No access token');
        useAuthStore.getState().setAccessToken(newToken);
        return newToken;
      })
      .catch(() => null)
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
}

function applyInterceptors(instance: typeof springApi | typeof ragApi | typeof fastApi) {
  // request
  instance.interceptors.request.use((config) => {
    const token = useAuthStore.getState().accessToken;
    if (isRefreshUrl(config.url)) {
      if (config.headers) delete config.headers.Authorization;
      return config;
    }
    if (token) setAuthHeader(config, token);
    return config;
  });

  // response
  instance.interceptors.response.use(
    (res) => res,
    async (error: AxiosError<{ code?: string; message?: string }>) => {
      const status = error.response?.status;
      const original = error.config as RetryAxiosRequestConfig;

      const requestUrl = original?.url ?? '';

      // refreshToken 재발급
      if (status === 401 && !shouldExcludeFromRefresh(requestUrl) && original && !original._retry) {
        original._retry = true;

        const newToken = await refreshAccessToken();
        if (newToken) {
          useAuthStore.getState().setAccessToken(newToken);
          setAuthHeader(original, newToken);

          return instance(original);
        } else {
          toast.error('세션이 만료되었습니다. 다시 로그인해주세요.');
          useAuthStore.getState().logout();
        }
      }

      // error UI
      const httpStatus = error.response?.status ?? 0;
      const code = error.response?.data?.code;
      const backendMessage = error.response?.data?.message;

      const msg =
        (code && ERROR_MESSAGES[code]) || backendMessage || ERROR_MESSAGES.INTERNAL_SERVER_ERROR;

      switch (httpStatus) {
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
          break;
      }

      return Promise.reject(error);
    }
  );
}

[springApi, ragApi, fastApi].forEach(applyInterceptors);
export default springApi;
