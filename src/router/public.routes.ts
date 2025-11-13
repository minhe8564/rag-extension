import { createElement, lazy, Suspense } from 'react';
import type { RouteObject } from 'react-router-dom';
import PublicLayout from '@/layouts/PublicLayout';

const Login = lazy(() => import('@/domains/auth/pages/Login'));
const Signup = lazy(() => import('@/domains/auth/pages/Signup'));
const Logout = lazy(() => import('@/domains/auth/pages/Logout'));

const FallbackDiv = createElement(
  'div',
  { className: 'flex h-screen items-center justify-center text-gray-600' },
  '로딩 중...'
);

export const publicRoutes: RouteObject = {
  element: createElement(Suspense, { fallback: FallbackDiv }, createElement(PublicLayout)),
  children: [
    { path: '/login', element: createElement(Login) },
    { path: '/signup', element: createElement(Signup) },
    { path: '/logout', element: createElement(Logout) },
  ],
};
