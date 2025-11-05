import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/domains/auth/store/auth.store';

export default function RequireAuth() {
  const { accessToken } = useAuthStore();
  const location = useLocation();

  if (!accessToken) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return <Outlet />;
}
