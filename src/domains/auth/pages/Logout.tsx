import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/domains/auth/store/auth.store';

export default function Logout() {
  const navigate = useNavigate();

  useEffect(() => {
    (async () => {
      try {
        await useAuthStore.getState().logout();
      } catch (err) {
        console.warn('Logout error ignored:', err);
      } finally {
        useAuthStore.getState().logout?.();
        navigate('/login', { replace: true });
      }
    })();
  }, [navigate]);

  return (
    <div className="flex h-screen items-center justify-center text-gray-500">
      로그아웃 중입니다...
    </div>
  );
}
