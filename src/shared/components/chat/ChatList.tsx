import { useEffect, useRef, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { getSessions, deleteSession, updateSession } from '@/shared/api/chat.api';
import type { SessionItem, ListSessionsResult } from '@/shared/types/chat.types';
import type { ApiEnvelope } from '@/shared/lib/api.types';
import { PencilLine, Trash2, Check, X, Loader2, ChevronDown, Clock } from 'lucide-react';
import Tooltip from '@/shared/components/Tooltip';
import ConfirmModal from '@/shared/components/ConfirmModal';
import { toast } from 'react-toastify';
import clsx from 'clsx';
import { formatIsoDatetime } from '@/shared/util/iso';

type ChatListProps = {
  activeSessionNo?: string;
  onSelect?: (session: SessionItem) => void;
  pageSize?: number;
};

export default function ChatList({ activeSessionNo, onSelect, pageSize = 20 }: ChatListProps) {
  const qc = useQueryClient();
  const [pageNum, setPageNum] = useState(0);
  const [items, setItems] = useState<SessionItem[]>([]);
  const [hasNext, setHasNext] = useState(true);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState('');
  const inputRef = useRef<HTMLInputElement | null>(null);
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

  const { mutate: mutateDelete, isPending: deleting } = useMutation({
    mutationFn: async (sessionNo: string) => (await deleteSession(sessionNo)).data,
    onSuccess: (_data, sessionNo) => {
      toast.success('삭제 완료했습니다.');
      setItems((prev) => prev.filter((s) => s.sessionNo !== sessionNo));
      if (pendingDelete?.sessionNo === sessionNo) {
        setPendingDelete(null);
      }
      if (localActiveNo === sessionNo) setLocalActiveNo(null);
      setConfirmOpen(false);
      setPageNum(0);
      qc.invalidateQueries({ queryKey: ['sessions'] });
      refetch();
    },
  });

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
      setEditingId(null);
      setEditingTitle('');
      qc.invalidateQueries({ queryKey: ['sessions'] });
    },
  });

  const startEdit = (session: SessionItem) => {
    setEditingId(session.sessionNo);
    setEditingTitle(session.title || '');
    setTimeout(() => inputRef.current?.focus(), 0);
  };
  const cancelEdit = () => {
    setEditingId(null);
    setEditingTitle('');
  };
  const submitEdit = (sessionNo: string) => {
    const v = editingTitle.trim();
    if (!v) return toast.warn('제목을 입력해주세요.');
    mutateRename({ sessionNo, title: v });
  };

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
              {items.map((session) => {
                const isEditing = editingId === session.sessionNo;
                const isActive = (no: string) => (activeSessionNo ?? localActiveNo) === no;

                return (
                  <li
                    key={session.sessionNo}
                    data-active={isActive(session.sessionNo) ? '1' : '0'}
                    className={clsx(
                      'group flex items-center rounded-md gap-2 px-3 py-2',
                      isActive(session.sessionNo)
                        ? 'bg-[var(--color-retina-bg)]'
                        : 'hover:bg-gray-50'
                    )}
                  >
                    <button
                      onClick={() => {
                        setLocalActiveNo(session.sessionNo);
                        onSelect?.(session);
                      }}
                      className="flex-1 text-left"
                      disabled={isEditing}
                    >
                      {isEditing ? (
                        <div className="flex items-center gap-2">
                          <input
                            ref={inputRef}
                            value={editingTitle}
                            onChange={(e) => setEditingTitle(e.target.value)}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') submitEdit(session.sessionNo);
                              if (e.key === 'Escape') cancelEdit();
                            }}
                            className="w-full rounded-md border px-2.5 py-1.5 text-sm outline-none focus:outline-none focus:ring-0 focus:border-gray-400"
                          />
                        </div>
                      ) : (
                        <>
                          <div className="line-clamp-1 mb-1 text-sm font-medium text-gray-800">
                            {session.title || '제목 없음'}
                          </div>
                          <div className="inline-flex items-center text-xs text-gray-500 gap-1">
                            <Clock size={12} />
                            {formatIsoDatetime(session.updatedAt || session.createdAt)}
                          </div>
                        </>
                      )}
                    </button>

                    <div className="flex items-center gap-1">
                      {isEditing ? (
                        <>
                          <Tooltip content="저장" side="bottom">
                            <button
                              onClick={() => submitEdit(session.sessionNo)}
                              disabled={renaming}
                              className="rounded-md p-1.5 text-[var(--color-retina)] hover:bg-white"
                            >
                              {renaming ? (
                                <Loader2 className="animate-spin" size={16} />
                              ) : (
                                <Check size={16} />
                              )}
                            </button>
                          </Tooltip>
                          <Tooltip content="취소" side="bottom">
                            <button
                              onClick={cancelEdit}
                              className="rounded-md p-1.5 text-gray-500 hover:bg-white"
                            >
                              <X size={16} />
                            </button>
                          </Tooltip>
                        </>
                      ) : (
                        <>
                          <Tooltip content="이름 변경" side="bottom">
                            <button
                              onClick={() => startEdit(session)}
                              className="hidden rounded-md p-1.5 text-gray-500 hover:bg-white group-hover:block"
                            >
                              <PencilLine size={16} />
                            </button>
                          </Tooltip>
                          <Tooltip content="삭제" side="bottom">
                            <button
                              onClick={() => requestDelete(session)}
                              className="hidden rounded-md p-1.5 text-red-500 hover:bg-white group-hover:block"
                              disabled={deleting && pendingDelete?.sessionNo === session.sessionNo}
                            >
                              <Trash2 size={16} />
                            </button>
                          </Tooltip>
                        </>
                      )}
                    </div>
                  </li>
                );
              })}
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
        message={`정말 삭제할까요?\n"${pendingDelete?.title || '제목 없음'}"\n[SessionNo] ${pendingDelete?.sessionNo ?? ''}`}
        confirmText={deleting ? '삭제 중...' : '삭제'}
        cancelText="취소"
        variant="danger"
        zIndex={10080}
      />
    </div>
  );
}
