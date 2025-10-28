import axios from 'axios';
import { useAuthStore } from '@/domains/auth/store/auth.store';

const apiInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000',
  withCredentials: true,
  timeout: 10000,
});

apiInstance.interceptors.request.use(config => {
  const token = useAuthStore.getState().accessToken;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

apiInstance.interceptors.response.use(
  res => res,
  error => {
    const status = error?.response?.status;

    switch (status) {
      case 400:
        alert('입력값을 확인해주세요.');
        break;
      case 401:
        useAuthStore.getState().logout();
        alert('세션이 만료되었습니다. 다시 로그인해주세요.');
        break;
      case 403:
        alert('접근 권한이 없습니다.');
        break;
      case 404:
        alert('요청한 정보를 찾을 수 없습니다.');
        break;
      case 500:
        alert('서버 오류가 발생했습니다.');
        break;
      default:
        console.error('API 오류:', error);
    }

    return Promise.reject(error);
  }
);

export default apiInstance;
