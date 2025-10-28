import { lazy, Suspense } from 'react';

const NotFound = lazy(() => import('@/shared/pages/NotFound'));

const Fallback = () => (
  <div className="flex h-[50vh] items-center justify-center text-gray-600">로딩 중...</div>
);

export const notFoundRoute = {
  path: '*',
  element: (
    <Suspense fallback={<Fallback />}>
      <NotFound />
    </Suspense>
  ),
};
