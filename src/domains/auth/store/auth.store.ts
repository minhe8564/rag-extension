import { create } from 'zustand';
import apiInstance from '@/shared/lib/apiInstance';

type Role = 'ADMIN' | 'USER';
interface User {
  email: string;
  nickname?: string;
  role: Role;
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  role: Role | null;
  initializing: boolean;

  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  setRole: (role: Role) => void;
}

export const useAuthStore = create<AuthState>(set => ({
  user: null,
  accessToken: null,
  role: null,
  initializing: false,

  // 로그인
  login: async (email, password) => {
    try {
      const res = await apiInstance.post('/auth/login', { email, password });
      const { accessToken, user } = res.data;

      set({
        accessToken,
        user,
        role: user.role,
      });
    } catch (err) {
      alert('로그인에 실패했습니다.');
      throw err;
    }
  },

  // 로그아웃
  logout: () => {
    set({
      user: null,
      accessToken: null,
      role: null,
    });
  },

  // 테스트용: 역할 설정
  setRole: role => set({ role }),
}));
