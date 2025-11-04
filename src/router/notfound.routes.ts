import { createElement, lazy, Suspense } from 'react';
import type { RouteObject } from 'react-router-dom';

const NotFound = lazy(() => import('@/shared/pages/NotFound'));

const FallbackDiv = createElement(
  'div',
  { className: 'flex h-[50vh] items-center justify-center text-gray-600' },
  '로딩 중...'
);

export const notFoundRoute: RouteObject = {
  path: '*',
  element: createElement(Suspense, { fallback: FallbackDiv }, createElement(NotFound)),
};
