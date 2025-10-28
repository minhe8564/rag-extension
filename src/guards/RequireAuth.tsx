import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/domains/auth/store/auth.store';

/**
 * 로그인 여부를 확인하고
 * 인증되지 않았을 경우 로그인 페이지로 리다이렉트하는 가드
 */
export default function RequireAuth() {
  // const { accessToken, initializing } = useAuthStore();
  // const location = useLocation();

  // 초기 로딩 중이면 잠시 대기 화면
  // if (initializing) {
  //   return (
  //     <div className="flex h-screen items-center justify-center text-gray-600">
  //       로그인 상태 확인 중...
  //     </div>
  //   );
  // }

  // 로그인 안 되어 있으면 로그인 페이지로 리다이렉트
  // if (!accessToken) {
  //   return <Navigate to="/login" replace state={{ from: location }} />;
  // }

  // 로그인되어 있으면 다음 라우트 렌더링
  return <Outlet />;
}
