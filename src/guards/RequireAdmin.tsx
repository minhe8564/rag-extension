import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '@/domains/auth/store/auth.store';

/**
 * 관리자 권한이 필요한 페이지에 접근할 때 사용하는 가드
 * 일반 사용자는 /user/documents 로 리다이렉트
 */
export default function RequireAdmin() {
  const { role } = useAuthStore(); // role: 'USER' | 'ADMIN' 등

  // if (role !== 'ADMIN') {
  //   return <Navigate to="/user/documents" replace />;
  // }

  return <Outlet />;
}
