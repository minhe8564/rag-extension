import { Navigate, createBrowserRouter } from 'react-router-dom';
import { publicRoutes } from '@/router/public.routes.ts';
import { adminRoutes } from '@/router/admin.routes.ts';
import { userRoutes } from '@/router/user.routes.ts';
import { notFoundRoute } from '@/router/notfound.routes.ts';

export const router = createBrowserRouter([
  { path: '/', element: <Navigate to="/login" replace /> },
  publicRoutes,
  adminRoutes,
  userRoutes,
  notFoundRoute,
]);
