import { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import RequireAuth from './routes/RequireAuth';
import RequireAdmin from './routes/RequireAdmin';

import PublicLayout from './layouts/PublicLayout';
import AdminLayout from './layouts/AdminLayout';
import UserLayout from './layouts/UserLayout';

const Login = lazy(() => import('./pages/auth/Login'));
const Signup = lazy(() => import('./pages/auth/Signup'));

const AdminDashboard = lazy(() => import('./pages/admin/Dashboard'));
const AdminDocuments = lazy(() => import('./pages/admin/Documents'));
const AdminRagTest = lazy(() => import('./pages/admin/RagTest'));
const AdminRagSettings = lazy(() => import('./pages/admin/RagSettings'));

const UserTextChat = lazy(() => import('./pages/user/TextChat'));
const UserImageChat = lazy(() => import('./pages/user/ImageChat'));
const UserDocuments = lazy(() => import('./pages/app/Documents'));

const NotFound = lazy(() => import('./pages/NotFound'));

export default function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<div>로딩 중...</div>}>
        <Routes>
          <Route path="/" element={<Navigate to="/login" replace />} />

          <Route element={<PublicLayout />}>
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
          </Route>

          <Route
            element={
              <RequireAuth>
                <RequireAdmin>
                  <AdminLayout />
                </RequireAdmin>
              </RequireAuth>
            }
          >
            <Route path="/admin/dashboard" element={<AdminDashboard />} />
            <Route path="/admin/documents" element={<AdminDocuments />} />
            <Route path="/admin/rag/test" element={<AdminRagTest />} />
            <Route path="/admin/rag/settings" element={<AdminRagSettings />} />
          </Route>

          <Route
            element={
              <RequireAuth>
                <UserLayout />
              </RequireAuth>
            }
          >
            <Route path="/user/chat/text" element={<UserTextChat />} />
            <Route path="/user/chat/image" element={<UserImageChat />} />
            <Route path="/user/documents" element={<UserDocuments />} />
          </Route>

          <Route path="*" element={<NotFound />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}
