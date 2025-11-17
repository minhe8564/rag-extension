import { lazy, Suspense } from 'react';
import type { RouteObject } from 'react-router-dom';
import PublicLayout from '@/layouts/PublicLayout';

const Login = lazy(() => import('@/domains/auth/pages/Login'));
const Signup = lazy(() => import('@/domains/auth/pages/Signup'));
const Logout = lazy(() => import('@/domains/auth/pages/Logout'));

const FallbackDiv = (
  <div className="flex h-screen items-center justify-center text-gray-600">로딩 중...</div>
);

export const publicRoutes: RouteObject = {
  element: (
    <Suspense fallback={FallbackDiv}>
      <PublicLayout />
    </Suspense>
  ),
  children: [
    { path: '/login', element: <Login /> },
    { path: '/signup', element: <Signup /> },
    { path: '/logout', element: <Logout /> },
  ],
};
