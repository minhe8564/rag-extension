import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '@/domains/auth/store/auth.store';

export default function RequireAdmin() {
  const { role } = useAuthStore();

  if (role == null) {
    return null;
  }

  if (role !== 'ADMIN') {
    return <Navigate to="/user/chat/text" replace />;
  }

  return <Outlet />;
}
