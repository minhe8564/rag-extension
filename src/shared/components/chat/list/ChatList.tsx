import { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { getSessions, deleteSession, updateSession } from '@/shared/api/chat.api';
import type { SessionItem, ListSessionsResult } from '@/shared/types/chat.types';
import type { ApiEnvelope } from '@/shared/lib/api.types';
import { ChevronDown, Loader2 } from 'lucide-react';
import Tooltip from '@/shared/components/Tooltip';
import ConfirmModal from '@/shared/components/ConfirmModal';
import { toast } from 'react-toastify';
import clsx from 'clsx';
import ChatListItem from '@/shared/components/chat/list/ChatListItem';

type Brand = 'retina' | 'hebees';

type ChatListProps = {
  activeSessionNo?: string;
  onSelect?: (session: SessionItem) => void;
  pageSize?: number;
  brand?: Brand;
};

export default function ChatList({
  activeSessionNo,
  onSelect,
  pageSize = 20,
  brand = 'retina',
}: ChatListProps) {
  const qc = useQueryClient();
  const [pageNum, setPageNum] = useState(0);
  const [items, setItems] = useState<SessionItem[]>([]);
  const [hasNext, setHasNext] = useState(true);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [pendingDelete, setPendingDelete] = useState<SessionItem | null>(null);
  const [localActiveNo, setLocalActiveNo] = useState<string | null>(null);

  const [collapsed, setCollapsed] = useState<boolean>(() => {
    const v = localStorage.getItem('chatlist:collapsed');
    return v === '1';
  });
  const toggleCollapsed = () => {
    setCollapsed((prev) => {
      const next = !prev;
      localStorage.setItem('chatlist:collapsed', next ? '1' : '0');
      return next;
    });
  };

  const { data, isFetching, isError, refetch } = useQuery<ApiEnvelope<ListSessionsResult>>({
    queryKey: ['sessions', pageNum, pageSize],
    queryFn: async () => {
      const res = await getSessions({ pageNum, pageSize });
      return res.data as ApiEnvelope<ListSessionsResult>;
    },
    placeholderData: (prev) => prev,
    staleTime: 15_000,
  });

  useEffect(() => {
    if (!data) return;
    const env = data.result ?? (data as unknown as ListSessionsResult);
    const list = Array.isArray(env?.data) ? env.data : [];
    const p = env?.pagination as
      | { totalPages?: number; pageNum?: number; hasNext?: boolean }
      | undefined;

    const next =
      typeof p?.hasNext === 'boolean'
        ? p.hasNext
        : typeof p?.totalPages === 'number' && typeof p?.pageNum === 'number'
          ? p.pageNum + 1 < p.totalPages
          : false;

    if (pageNum === 0) {
      setItems(list);
      setHasNext(next);
    }
  }, [data, pageNum]);

  useEffect(() => {
    setPageNum(0);
  }, []);

  useEffect(() => {
    if (!localActiveNo && activeSessionNo) {
      document.querySelector(`[data-active="1"]`)?.scrollIntoView({ block: 'nearest' });
    }
  }, [activeSessionNo, localActiveNo]);

  const loadMore = async () => {
    if (!hasNext || isFetching) return;
    const nextPage = pageNum + 1;
    try {
      const res = await getSessions({ pageNum: nextPage, pageSize });
      const env = (res.data.result ?? res.data) as ListSessionsResult;
      const list = Array.isArray(env?.data) ? env.data : [];
      const p = env?.pagination as
        | { totalPages?: number; pageNum?: number; hasNext?: boolean }
        | undefined;

      const next =
        typeof p?.hasNext === 'boolean'
          ? p.hasNext
          : typeof p?.totalPages === 'number' && typeof p?.pageNum === 'number'
            ? p.pageNum + 1 < p.totalPages
            : false;

      setItems((prev) => [...prev, ...list]);
      setHasNext(next);
      setPageNum(nextPage);
    } catch {
      toast.error('목록을 불러오는 중 오류가 발생했습니다.');
    }
  };

  // 삭제
  const { mutate: mutateDelete, isPending: deleting } = useMutation({
    mutationFn: async (sessionNo: string) => (await deleteSession(sessionNo)).data,
    onSuccess: (_data, sessionNo) => {
      toast.success('삭제 완료했습니다.');
      setItems((prev) => prev.filter((s) => s.sessionNo !== sessionNo));
      if (pendingDelete?.sessionNo === sessionNo) setPendingDelete(null);
      if (localActiveNo === sessionNo) setLocalActiveNo(null);
      setConfirmOpen(false);
      setPageNum(0);
      qc.invalidateQueries({ queryKey: ['sessions'] });
      refetch();
    },
  });

  // 제목 변경
  const { mutate: mutateRename, isPending: renaming } = useMutation({
    mutationFn: async ({ sessionNo, title }: { sessionNo: string; title: string }) =>
      (await updateSession(sessionNo, { title })).data,
    onSuccess: (_data, variables) => {
      toast.success('제목을 변경했습니다.');
      setItems((prev) =>
        prev.map((s) =>
          s.sessionNo === variables.sessionNo ? { ...s, title: variables.title } : s
        )
      );
      qc.invalidateQueries({ queryKey: ['sessions'] });
    },
  });

  const requestDelete = (session: SessionItem) => {
    setPendingDelete(session);
    setConfirmOpen(true);
  };
  const handleCloseConfirm = () => {
    setConfirmOpen(false);
    setPendingDelete(null);
  };
  const handleConfirmDelete = () => {
    if (!pendingDelete) return;
    mutateDelete(pendingDelete.sessionNo);
  };

  useEffect(() => {
    setLocalActiveNo(activeSessionNo ?? null);
  }, [activeSessionNo]);

  const isLoadingInitial = isFetching && pageNum === 0;
  const activeNo = activeSessionNo ?? localActiveNo;

  return (
    <div className="flex h-full flex-col bg-white">
      {items.length > 0 && (
        <div className="flex items-center justify-between px-3 py-2 overflow-visible">
          <div className="text-sm font-semibold text-gray-700">
            채팅 목록 <span className="text-gray-400">({items.length})</span>
          </div>

          <Tooltip
            content={collapsed ? '채팅 목록 펼치기' : '채팅 목록 접기'}
            side="bottom"
            shiftX={15}
          >
            <button
              onClick={toggleCollapsed}
              className="inline-flex items-center gap-1 rounded-md px-1 py-1 text-xs text-gray-600 hover:bg-gray-100"
              aria-expanded={!collapsed}
              aria-label={collapsed ? '펼치기' : '접기'}
            >
              <ChevronDown
                size={16}
                className={clsx(
                  'transition-transform duration-200',
                  collapsed ? '-rotate-90' : 'rotate-0'
                )}
              />
            </button>
          </Tooltip>
        </div>
      )}

      <div className="relative min-h-[120px] flex-1 mt-1">
        {!isLoadingInitial && !isError && items.length === 0 && null}

        {!collapsed && (
          <>
            <ul>
              {items.map((session) => (
                <ChatListItem
                  key={session.sessionNo}
                  session={session}
                  isActive={activeNo === session.sessionNo}
                  onSelect={(s) => {
                    setLocalActiveNo(s.sessionNo);
                    onSelect?.(s);
                  }}
                  onRename={(title) => mutateRename({ sessionNo: session.sessionNo, title })}
                  onRequestDelete={() => requestDelete(session)}
                  renaming={renaming}
                  deleting={deleting && pendingDelete?.sessionNo === session.sessionNo}
                  brand={brand}
                />
              ))}
            </ul>

            {items.length > 0 && hasNext && (
              <div className="flex items-center justify-center p-3">
                <button
                  onClick={loadMore}
                  disabled={isFetching}
                  className="inline-flex items-center gap-2 rounded-md border px-3 py-1.5 text-sm hover:bg-gray-50 disabled:opacity-60"
                >
                  {isFetching ? <Loader2 className="animate-spin" size={16} /> : null}
                  더보기
                </button>
              </div>
            )}
          </>
        )}
      </div>

      <ConfirmModal
        open={confirmOpen}
        onClose={handleCloseConfirm}
        onConfirm={handleConfirmDelete}
        title="채팅 삭제"
        message={`정말 삭제할까요?\n"${pendingDelete?.title || '제목 없음'}"\n`}
        confirmText={deleting ? '삭제 중...' : '삭제'}
        cancelText="취소"
        variant="danger"
        zIndex={10080}
      />
    </div>
  );
}
