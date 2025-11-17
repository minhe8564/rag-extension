import { lazy, Suspense } from 'react';
import type { RouteObject } from 'react-router-dom';

const NotFound = lazy(() => import('@/shared/pages/NotFound'));

const FallbackDiv = (
  <div className="flex h-[50vh] items-center justify-center text-gray-600">로딩 중...</div>
);

export const notFoundRoute: RouteObject = {
  path: '*',
  element: (
    <Suspense fallback={FallbackDiv}>
      <NotFound />
    </Suspense>
  ),
};
