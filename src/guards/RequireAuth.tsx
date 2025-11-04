import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/domains/auth/store/auth.store';

export default function RequireAuth() {
  const { accessToken, initializing } = useAuthStore();
  const location = useLocation();

  if (initializing) {
    return (
      <div className="flex h-screen items-center justify-center text-gray-600">
        로그인 상태 확인 중...
      </div>
    );
  }

  if (!accessToken) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return <Outlet />;
}
