import { lazy, Suspense } from 'react';
import RequireAuth from '@/guards/RequireAuth';
import RequireAdmin from '@/guards/RequireAdmin';
import AdminLayout from '@/layouts/AdminLayout';

const AdminDashboard = lazy(() => import('@/domains/admin/pages/Dashboard'));
const AdminDocuments = lazy(() => import('@/domains/admin/pages/Documents'));
const AdminChat = lazy(() => import('@/domains/admin/pages/TextChat'));
const AdminRagTest = lazy(() => import('@/domains/admin/pages/RagTest'));
const AdminRagSettings = lazy(() => import('@/domains/admin/pages/RagSettings'));
const AdminUsers = lazy(() => import('@/domains/admin/pages/Users'));

const Fallback = () => (
  <div className="flex h-screen items-center justify-center text-gray-600">로딩 중...</div>
);

export const adminRoutes = {
  element: <RequireAuth />,
  children: [
    {
      element: <RequireAdmin />,
      children: [
        {
          element: (
            <Suspense fallback={<Fallback />}>
              <AdminLayout />
            </Suspense>
          ),
          children: [
            { path: '/admin/dashboard', element: <AdminDashboard /> },
            { path: '/admin/documents', element: <AdminDocuments /> },
            { path: '/admin/chat', element: <AdminChat /> },
            { path: '/admin/rag/test', element: <AdminRagTest /> },
            { path: '/admin/rag/settings', element: <AdminRagSettings /> },
            { path: '/admin/users', element: <AdminUsers /> },
          ],
        },
      ],
    },
  ],
};
