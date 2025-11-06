import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
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

  login: (email: string, password: string) => Promise<string>;
  logout: () => void;
  setAccessToken: (token: string) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      role: null,

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

      setAccessToken: (token) => set({ accessToken: token }),
    }),
    {
      name: 'auth-store',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        role: state.role,
      }),
    }
  )
);
