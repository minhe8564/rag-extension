import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/domains/auth/store/auth.store';
import { useEffect } from 'react';

export default function RequireAuth() {
  const { accessToken, role } = useAuthStore();
  const location = useLocation();

  useEffect(() => {
  }, [location.pathname, accessToken, role]);

  if (!accessToken) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return <Outlet />;
}
