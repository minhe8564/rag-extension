// src/router/user.routes.ts
import { createElement, lazy, Suspense } from 'react';
import type { RouteObject } from 'react-router-dom';
import { Navigate } from 'react-router-dom';
import RequireAuth from '@/guards/RequireAuth';
import UserLayout from '@/layouts/UserLayout';

const UserTextChat = lazy(() => import('@/domains/user/pages/TextChat'));
const UserImageChat = lazy(() => import('@/domains/user/pages/ImageGenerator'));
const UserDocuments = lazy(() => import('@/domains/user/pages/Documents'));
const UserProfile = lazy(() => import('@/domains/user/pages/Profile'));

const FallbackDiv = createElement(
  'div',
  { className: 'flex h-screen items-center justify-center text-gray-600' },
  '로딩 중...'
);

export const userRoutes: RouteObject = {
  path: '/user',
  element: createElement(RequireAuth),
  children: [
    {
      element: createElement(Suspense, { fallback: FallbackDiv }, createElement(UserLayout)),
      children: [
        { index: true, element: createElement(Navigate, { to: 'chat/text', replace: true }) },
        { path: 'chat/text', element: createElement(UserTextChat) },
        { path: 'chat/text/:sessionNo', element: createElement(UserTextChat) },
        { path: 'chat/image', element: createElement(UserImageChat) },
        { path: 'documents', element: createElement(UserDocuments) },
        { path: 'profile', element: createElement(UserProfile) },
      ],
    },
  ],
};
