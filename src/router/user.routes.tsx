import { lazy, Suspense } from 'react';
import RequireAuth from '@/guards/RequireAuth';
import UserLayout from '@/layouts/UserLayout';

const UserTextChat = lazy(() => import('@/domains/user/pages/TextChat'));
const UserImageChat = lazy(() => import('@/domains/user/pages/ImageChat'));
const UserDocuments = lazy(() => import('@/domains/user/pages/Documents'));

const Fallback = () => (
  <div className="flex h-screen items-center justify-center text-gray-600">로딩 중...</div>
);

export const userRoutes = {
  element: <RequireAuth />,
  children: [
    {
      element: (
        <Suspense fallback={<Fallback />}>
          <UserLayout />
        </Suspense>
      ),
      children: [
        { path: '/user/chat/text', element: <UserTextChat /> },
        { path: '/user/chat/image', element: <UserImageChat /> },
        { path: '/user/documents', element: <UserDocuments /> },
      ],
    },
  ],
};
