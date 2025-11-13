import { createElement, lazy, Suspense } from 'react';
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
            { index: true, element: createElement(Navigate, { to: 'dashboard', replace: true }) },
            { path: 'dashboard', element: createElement(AdminDashboard) },
            { path: 'rag/settings', element: createElement(AdminRagSettings) },
            { path: 'rag/test', element: createElement(AdminRagTest) },
            { path: 'rag/text', element: createElement(AdminChat) },
            { path: 'rag/text/:sessionNo', element: createElement(AdminChat) },
            { path: 'chat/image', element: createElement(AdminImageChat) },
            { path: 'documents', element: createElement(AdminDocuments) },
            { path: 'users', element: createElement(AdminUsers) },
            { path: 'profile', element: createElement(AdminProfile) },
          ],
        },
      ],
    },
  ],
};
