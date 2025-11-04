import { createElement, lazy, Suspense } from 'react';
import type { RouteObject } from 'react-router-dom';
import RequireAuth from '@/guards/RequireAuth';
import RequireAdmin from '@/guards/RequireAdmin';
import AdminLayout from '@/layouts/AdminLayout';

const AdminDashboard = lazy(() => import('@/domains/admin/pages/Dashboard'));
const AdminDocuments = lazy(() => import('@/domains/admin/pages/Documents'));
const AdminChat = lazy(() => import('@/domains/admin/pages/TextChat'));
const AdminRagTest = lazy(() => import('@/domains/admin/pages/RagTest'));
const AdminRagSettings = lazy(() => import('@/domains/admin/pages/RagSettings'));
const AdminUsers = lazy(() => import('@/domains/admin/pages/Users'));
const AdminProfile = lazy(() => import('@/domains/admin/pages/Profile'));

const FallbackDiv = createElement(
  'div',
  { className: 'flex h-screen items-center justify-center text-gray-600' },
  '로딩 중...'
);

export const adminRoutes: RouteObject = {
  path: '/admin',
  element: createElement(RequireAuth),
  children: [
    {
      element: createElement(RequireAdmin),
      children: [
        {
          element: createElement(Suspense, { fallback: FallbackDiv }, createElement(AdminLayout)),
          children: [
            { index: true, element: createElement(AdminDashboard) },
            { path: 'dashboard', element: createElement(AdminDashboard) },
            { path: 'documents', element: createElement(AdminDocuments) },
            { path: 'chat', element: createElement(AdminChat) },
            { path: 'rag/test', element: createElement(AdminRagTest) },
            { path: 'rag/settings', element: createElement(AdminRagSettings) },
            { path: 'users', element: createElement(AdminUsers) },
            { path: 'profile', element: createElement(AdminProfile) },
          ],
        },
      ],
    },
  ],
};
