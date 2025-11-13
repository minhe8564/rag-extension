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

const PAGE_SIZE = 20;

export type ChatOwner = 'user' | 'admin';

const key = (owner: ChatOwner, pageNum = 0, pageSize = PAGE_SIZE) =>
  ['sessions', owner, pageNum, pageSize] as const;

const buildChatPath = (owner: ChatOwner, sessionNo: string) =>
  owner === 'admin' ? `/admin/chat/text/${sessionNo}` : `/user/chat/text/${sessionNo}`;

const derive = (pathname: string, searchParams: URLSearchParams, paramsSessionNo?: string) => {
  if (paramsSessionNo) return paramsSessionNo;
  const byQuery = searchParams.get('session');
  if (byQuery) return byQuery;
  const legacy = pathname.match(/\/chat\/text:session=([^/]+)/);
  return legacy?.[1] ?? null;
};

export function useDerivedSessionNo(
  location: Location,
  searchParams: URLSearchParams,
  paramsSessionNo?: string,
  owner: ChatOwner = 'user'
) {
  const derived = useMemo(
    () => derive(location.pathname, searchParams, paramsSessionNo),
    [location.pathname, searchParams, paramsSessionNo]
  );

  useEffect(() => {
    if (!derived) return;

    const needNormalize =
      location.pathname.includes('text:session=') || location.search.includes('session=');

    const targetPath = buildChatPath(owner, derived);
    const currentFull = location.pathname + location.search;

    if (needNormalize && currentFull !== targetPath) {
      window.history.replaceState(history.state, '', targetPath);
    }
  }, [derived, location.pathname, location.search, owner]);

  return derived;
}

export function useEnsureSession(
  setCurrentSessionNo: (v: string) => void,
  owner: ChatOwner = 'user'
) {
  const qc = useQueryClient();

  return async (opts?: { llm?: string; query?: string }) => {
    const tempId = `temp-${Date.now()}`;
    const nowIso = new Date().toISOString();

    const tempSession: SessionItem = {
      sessionNo: tempId,
      title: '새 채팅',
      createdAt: nowIso,
      llmNo: 0 as unknown as SessionItem['llmNo'],
      llmName: '' as unknown as SessionItem['llmName'],
      userNo: 0 as unknown as SessionItem['userNo'],
      userName: '' as unknown as SessionItem['userName'],
    };

    qc.setQueryData<ApiEnvelope<ListSessionsResult>>(key(owner, 0, PAGE_SIZE), (old) => {
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

      return {
        ...base,
        result: {
          ...env,
          data: [tempSession, ...prev],
          pagination: {
            ...env.pagination,
            pageNum: 0,
          },
        },
      };
    });

    setCurrentSessionNo(tempId);

    const payload: { llm?: string; query?: string } = {};
    if (opts?.llm) payload.llm = opts.llm;
    if (opts?.query) payload.query = opts.query;

    const created = await createSession(payload);
    const data: CreateSessionResult = created.data.result;

    const realId = data.sessionNo;
    const realTitle = data.title ?? '새 채팅';

    const realSession: SessionItem = {
      ...tempSession,
      sessionNo: realId,
      title: realTitle,
    };

    qc.setQueryData<ApiEnvelope<ListSessionsResult>>(key(owner, 0, PAGE_SIZE), (old) => {
      if (!old) return old;
      const env = old.result;

      const alreadyExists = env.data.some((s) => s.sessionNo === realId);
      const replaced = env.data.map((item) => (item.sessionNo === tempId ? realSession : item));
      const nextData = alreadyExists ? replaced.filter((s) => s.sessionNo !== tempId) : replaced;

      const prevTotal =
        typeof env.pagination?.totalItems === 'number' ? env.pagination.totalItems : 0;
      const nextTotal = alreadyExists ? prevTotal : prevTotal + 1;

      return {
        ...old,
        result: {
          ...env,
          data: nextData,
          pagination: {
            ...env.pagination,
            pageNum: 0,
            totalItems: nextTotal,
          },
        },
      };
    });

    qc.invalidateQueries({ queryKey: ['sessions', owner] });

    setCurrentSessionNo(realId);
    const nextPath = buildChatPath(owner, realId);
    window.history.replaceState(history.state, '', nextPath);
    document.title = realTitle;

    return realId;
  };
}

const messages = [
  '문서를 분석하고 있습니다…',
  '핵심 정보를 정리하는 중입니다…',
  '관련 내용을 탐색하고 있습니다…',
  '가장 적절한 답을 구성하고 있습니다…',
  '자료를 기반으로 답변을 조합하고 있습니다…',
  '근거를 기반으로 답변을 다듬고 있습니다…',
  'HEBEES RAG 답변 생성 중입니다…',
] as const;

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
