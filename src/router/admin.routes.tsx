import { lazy, Suspense } from 'react';
import type { RouteObject } from 'react-router-dom';
import { Navigate } from 'react-router-dom';
import RequireAuth from '@/guards/RequireAuth';
import RequireAdmin from '@/guards/RequireAdmin';
import AdminLayout from '@/layouts/AdminLayout';

const AdminDashboard = lazy(() => import('@/domains/admin/pages/Dashboard'));
const AdminRagSettings = lazy(() => import('@/domains/admin/pages/RagSettings'));
const AdminRagTest = lazy(() => import('@/domains/admin/pages/RagTest'));
const AdminChat = lazy(() => import('@/domains/admin/pages/TextChat'));
const AdminImageChat = lazy(() => import('@/domains/admin/pages/ImageGenerator'));
const AdminDocuments = lazy(() => import('@/domains/admin/pages/Documents'));
const AdminUsers = lazy(() => import('@/domains/admin/pages/UsersManagement'));
const AdminProfile = lazy(() => import('@/domains/admin/pages/Profile'));

const FallbackDiv = (
  <div className="flex h-screen items-center justify-center text-gray-600">로딩 중...</div>
);

export const adminRoutes: RouteObject = {
  path: '/admin',
  element: <RequireAuth />,
  children: [
    {
      element: <RequireAdmin />,
      children: [
        {
          element: (
            <Suspense fallback={FallbackDiv}>
              <AdminLayout />
            </Suspense>
          ),
          children: [
            {
              index: true,
              element: <Navigate to="dashboard" replace />,
            },
            { path: 'dashboard', element: <AdminDashboard /> },
            { path: 'rag/settings', element: <AdminRagSettings /> },
            { path: 'rag/test', element: <AdminRagTest /> },
            { path: 'chat/text', element: <AdminChat /> },
            { path: 'chat/text/:sessionNo', element: <AdminChat /> },
            { path: 'chat/image', element: <AdminImageChat /> },
            { path: 'documents', element: <AdminDocuments /> },
            { path: 'users', element: <AdminUsers /> },
            { path: 'profile', element: <AdminProfile /> },
          ],
        },
      ],
    },
  ],
};
