import { lazy, Suspense } from 'react';
import PublicLayout from '@/layouts/PublicLayout';

const Login = lazy(() => import('@/domains/auth/pages/Login'));
const Signup = lazy(() => import('@/domains/auth/pages/Signup'));

const Fallback = ({ h = 'h-screen' }: { h?: string }) => (
  <div className={`flex ${h} items-center justify-center text-gray-600`}>로딩 중...</div>
);

export const publicRoutes = {
  element: (
    <Suspense fallback={<Fallback />}>
      <PublicLayout />
    </Suspense>
  ),
  children: [
    { path: '/login', element: <Login /> },
    { path: '/signup', element: <Signup /> },
  ],
};
