// import { Navigate, Outlet } from 'react-router-dom';
import { Outlet } from 'react-router-dom';
import { useAuthStore } from '@/domains/auth/store/auth.store';
import { Navigate } from 'react-router-dom';
import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

export default function RequireAdmin() {
  const { role, accessToken } = useAuthStore();
  const location = useLocation();

  useEffect(() => {
  }, [role, accessToken, location.pathname]);

  if (role == null) {
    return null;
  }

  if (role !== 'ADMIN') {
    return <Navigate to="/user/chat/text" replace />;
  }

  return <Outlet />;
}
