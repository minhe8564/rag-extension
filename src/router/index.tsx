import { Navigate, createBrowserRouter } from 'react-router-dom';
import { publicRoutes } from '@/router/public.routes';
import { adminRoutes } from '@/router/admin.routes';
import { userRoutes } from '@/router/user.routes';
import { notFoundRoute } from '@/router/notfound.routes';

export const router = createBrowserRouter([
  { path: '/', element: <Navigate to="/login" replace /> },
  publicRoutes,
  adminRoutes,
  userRoutes,
  notFoundRoute,
]);
