import { useEffect, useMemo, useState } from 'react';
import type { Location } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { createSession } from '@/shared/api/chat.api';
import type {
  CreateSessionResult,
  SessionItem,
  ListSessionsResult,
} from '@/shared/types/chat.types';
import type { ApiEnvelope } from '@/shared/lib/api.types';

// 세션 리스트 1페이지 key
const PAGE_SIZE = 20;
const key = (pageNum = 0, pageSize = PAGE_SIZE) => ['sessions', pageNum, pageSize] as const;

// URL에서 세션번호 추출
const derive = (pathname: string, searchParams: URLSearchParams, paramsSessionNo?: string) => {
  if (paramsSessionNo) return paramsSessionNo;
  const byQuery = searchParams.get('session');
  if (byQuery) return byQuery;
  const legacy = pathname.match(/\/chat\/text:session=([^/]+)/);
  return legacy?.[1] ?? null;
};

// 세션번호 파싱 + URL 정규화
export function useDerivedSessionNo(
  location: Location,
  searchParams: URLSearchParams,
  paramsSessionNo?: string
) {
  // 세션 값 계산
  const derived = useMemo(
    () => derive(location.pathname, searchParams, paramsSessionNo),
    [location.pathname, searchParams, paramsSessionNo]
  );

  // /user/chat/text?session=xxx → /user/chat/text/xxx 로 정규화
  useEffect(() => {
    if (!derived) return;
    const needNormalize =
      location.pathname.includes('text:session=') || location.search.includes('session=');
    const targetPath = `/user/chat/text/${derived}`;
    const currentFull = location.pathname + location.search;
    if (needNormalize && currentFull !== targetPath) {
      window.history.replaceState(history.state, '', targetPath);
    }
  }, [derived, location.pathname, location.search]);

  return derived;
}

// 세션 없으면 생성 + 목록 캐시에 즉시 추가
export function useEnsureSession(setCurrentSessionNo: (v: string) => void) {
  const qc = useQueryClient();

  return async () => {
    // 새 세션 만들기
    const created = await createSession({});
    const data: CreateSessionResult = created.data.result;
    const newItem = data as SessionItem;

    // 세션 리스트 1페이지 캐시 업데이트
    qc.setQueryData<ApiEnvelope<ListSessionsResult>>(key(0, PAGE_SIZE), (old) => {
      const base: ApiEnvelope<ListSessionsResult> = old ?? {
        status: 200,
        code: 'OK',
        message: '',
        isSuccess: true,
        result: {
          data: [],
          pagination: {
            pageNum: 0,
            pageSize: PAGE_SIZE,
            totalItems: 0,
            totalPages: 1,
            hasNext: true,
          },
        },
      };

      const env = base.result;
      const prev = Array.isArray(env.data) ? env.data : [];
      const exists = prev.some((s) => s.sessionNo === newItem.sessionNo);

      // 새 세션을 맨 위에 추가 (중복 제거)
      const nextData = [newItem, ...prev.filter((s) => s.sessionNo !== newItem.sessionNo)];

      return {
        ...base,
        result: {
          ...env,
          data: nextData,
          pagination: {
            ...env.pagination,
            pageNum: 0,
            totalItems: exists ? env.pagination.totalItems : env.pagination.totalItems + 1,
          },
        },
      };
    });

    // 다른 페이지들 invalidate
    qc.invalidateQueries({ queryKey: ['sessions'] });

    // URL 상태 갱신
    setCurrentSessionNo(data.sessionNo);
    window.history.replaceState(history.state, '', `/user/chat/text/${data.sessionNo}`);

    return data.sessionNo;
  };
}

// 답변 대기중 문구 순환
const messages = [
  '문서를 분석하고 있습니다…',
  '핵심 정보를 정리하는 중입니다…',
  '관련 내용을 탐색하고 있습니다…',
  '가장 적절한 답을 구성하고 있습니다…',
  '자료를 기반으로 답변을 조합하고 있습니다…',
  '근거를 기반으로 답변을 다듬고 있습니다…',
  'HEBEES RAG 답변 생성 중입니다…',
] as const;

// AI 응답 기다리는 동안 2초마다 문구 변경
export function useThinkingTicker(active: boolean) {
  const [idx, setIdx] = useState(0);

  useEffect(() => {
    if (!active) {
      setIdx(0);
      return;
    }
    const t = setInterval(() => setIdx((i) => (i + 1) % messages.length), 2000);
    return () => clearInterval(t);
  }, [active]);

  return messages[idx];
}
