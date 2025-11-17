import { lazy, Suspense } from 'react';
import type { RouteObject } from 'react-router-dom';
import { Navigate } from 'react-router-dom';
import RequireAuth from '@/guards/RequireAuth';
import UserLayout from '@/layouts/UserLayout';

const UserTextChat = lazy(() => import('@/domains/user/pages/TextChat'));
const UserImageChat = lazy(() => import('@/domains/user/pages/ImageGenerator'));
const UserDocuments = lazy(() => import('@/domains/user/pages/Documents'));
const UserProfile = lazy(() => import('@/domains/user/pages/Profile'));

const FallbackDiv = (
  <div className="flex h-screen items-center justify-center text-gray-600">로딩 중...</div>
);

export const userRoutes: RouteObject = {
  path: '/user',
  element: <RequireAuth />,
  children: [
    {
      element: (
        <Suspense fallback={FallbackDiv}>
          <UserLayout />
        </Suspense>
      ),
      children: [
        { index: true, element: <Navigate to="chat/text" replace /> },
        { path: 'chat/text', element: <UserTextChat /> },
        { path: 'chat/text/:sessionNo', element: <UserTextChat /> },
        { path: 'chat/image', element: <UserImageChat /> },
        { path: 'documents', element: <UserDocuments /> },
        { path: 'profile', element: <UserProfile /> },
      ],
    },
  ],
};
