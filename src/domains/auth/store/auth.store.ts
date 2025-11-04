import { create } from 'zustand';
import { login as apiLogin } from '@/domains/auth/api/auth.api';

interface AuthUser {
  name: string;
  roleName: string;
  businessType: number;
}

interface AuthState {
  user: AuthUser | null;
  accessToken: string | null;
  role: string | null;
  initializing: boolean;

  login: (email: string, password: string) => Promise<string>;
  logout: () => void;
}

export const useAuthStore = create<AuthState>(set => ({
  user: null,
  accessToken: null,
  role: null,
  initializing: false,

  login: async (email, password) => {
    const result = await apiLogin(email, password);

    set({
      user: {
        name: result.name,
        roleName: result.roleName,
        businessType: result.businessType,
      },
      accessToken: result.accessToken,
      role: result.roleName,
    });

    return result.roleName;
  },

  logout: () =>
    set({
      user: null,
      accessToken: null,
      role: null,
    }),
}));
