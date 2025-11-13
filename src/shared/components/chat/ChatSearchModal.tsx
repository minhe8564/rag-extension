import { useEffect, useRef, useState } from 'react';
import { Search, X, Clock, ChevronRight, Loader2 } from 'lucide-react';
import { createPortal } from 'react-dom';
import { getSessions } from '@/shared/api/chat.api';
import type { SessionItem, ListSessionsResult } from '@/shared/types/chat.types';
import { formatCreatedAt } from '@/shared/utils/date';

export type ChatSearchModalProps = {
  open: boolean;
  title?: string;
  value: string;
  placeholder?: string;
  onValueChange: (v: string) => void;
  onClose: () => void;
  onSelect: (session: SessionItem) => void;
};

export default function ChatSearchModal({
  open,
  title = '채팅 검색',
  value,
  placeholder = '채팅 제목 검색',
  onValueChange,
  onClose,
  onSelect,
}: ChatSearchModalProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const labelId = 'chat-search-modal-title';

  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [sessions, setSessions] = useState<SessionItem[]>([]);

  useEffect(() => {
    if (!open) return;
    const t = setTimeout(() => inputRef.current?.focus(), 0);
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose();
    document.addEventListener('keydown', onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', onKey);
      document.body.style.overflow = prev;
      clearTimeout(t);
    };
  }, [open, onClose]);

  const fetchSessions = async (q?: string) => {
    const resp = await getSessions({ pageNum: 0, pageSize: 20, query: q || undefined });
    const envelope = resp?.data;
    const result: ListSessionsResult | undefined = envelope?.result ?? envelope;
    return Array.isArray(result?.data) ? result!.data : [];
  };

  useEffect(() => {
    if (!open) return;
    let alive = true;

    (async () => {
      try {
        setLoading(true);
        setErrorMsg(null);
        const list = await fetchSessions(value.trim());
        if (!alive) return;
        setSessions(list);
      } catch {
        if (!alive) return;
        setErrorMsg('세션을 불러오는 데 실패했어요.');
        setSessions([]);
      } finally {
        if (alive) setLoading(false);
      }
    })();

    return () => {
      alive = false;
    };
  }, [open, value]);

  const handleOverlayClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) onClose();
  };

  const SessionRow = ({ s }: { s: SessionItem }) => (
    <li key={s.sessionNo}>
      <button
        onClick={() => {
          onSelect(s);
          onClose();
        }}
        className="group flex w-full items-center justify-between rounded-xl border border-transparent px-3 py-2 text-left transition hover:border-gray-200 hover:bg-gray-50"
        type="button"
      >
        <div className="min-w-0">
          <div className="truncate text-[13px] font-medium text-gray-800">{s.title}</div>
          <div className="mt-0.5 flex items-center gap-2 text-[11px] text-gray-500">
            <span className="inline-flex items-center gap-1">
              <Clock size={12} /> {formatCreatedAt(s.updatedAt)}
            </span>
          </div>
        </div>
        <ChevronRight
          size={16}
          className="shrink-0 text-gray-400 opacity-0 transition group-hover:opacity-100"
        />
      </button>
    </li>
  );

  const renderSection = () => {
    if (loading) {
      return (
        <div className="flex items-center justify-center py-8 text-gray-500">
          <Loader2 size={18} className="mr-2 animate-spin" />
          불러오는 중…
        </div>
      );
    }
    if (errorMsg) {
      return (
        <div className="rounded-xl border border-dashed border-gray-200 p-6 text-center text-sm text-gray-600">
          {errorMsg}
        </div>
      );
    }

    const searching = !!value.trim();
    const titleText = searching ? `검색 결과 ${sessions.length}건` : '최근 채팅';

    return (
      <div>
        <div
          className={`mb-2 ${searching ? 'text-[12px] text-gray-500' : 'text-xs font-semibold text-gray-700'}`}
        >
          {titleText}
        </div>

        {sessions.length === 0 ? (
          searching ? (
            <EmptyState query={value} />
          ) : (
            <div className="rounded-xl border border-dashed border-gray-200 p-6 text-center text-sm text-gray-600">
              최근 세션이 없어요.
            </div>
          )
        ) : (
          <ul className="space-y-1.5">
            {sessions.map((s) => (
              <SessionRow key={s.sessionNo} s={s} />
            ))}
          </ul>
        )}
      </div>
    );
  };

  if (!open) return null;

  return createPortal(
    <div
      className="fixed inset-0 z-[9998] bg-black/60 flex items-center justify-center p-4"
      onClick={handleOverlayClick}
      role="dialog"
      aria-modal="true"
      aria-labelledby={labelId}
    >
      <div className="relative w-full max-w-2xl rounded-2xl bg-white shadow-2xl ring-1 ring-black/5 overflow-hidden">
        <div className="flex items-center justify-between px-5 pt-4 pb-3">
          <span id={labelId} className="text-sm text-gray-700 font-medium">
            {title}
          </span>
          <button
            aria-label="닫기"
            onClick={onClose}
            className="ml-1 p-2 rounded-full bg-black/5 hover:bg-black/10 transition"
            type="button"
          >
            <X size={18} />
          </button>
        </div>

        <div className="px-5 pb-5">
          <div className="relative">
            <Search
              size={16}
              className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
            />
            <input
              ref={inputRef}
              value={value}
              onChange={(e) => onValueChange(e.target.value)}
              placeholder={placeholder}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && sessions.length > 0) {
                  onSelect(sessions[0]);
                  onClose();
                }
              }}
              className="w-full rounded-xl border border-gray-200 bg-white px-9 py-2.5 text-sm focus:outline-none focus:ring-0 focus:border-gray-400"
            />
            {!!value && (
              <button
                onClick={() => onValueChange('')}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 rounded-md p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
                aria-label="내용 지우기"
              >
                <X size={14} />
              </button>
            )}
          </div>

          <div className="mt-4 max-h-[48vh] overflow-auto pr-1">{renderSection()}</div>
        </div>
      </div>
    </div>,
    document.body
  );
}

function EmptyState({ query }: { query: string }) {
  return (
    <div className="rounded-xl border border-dashed border-gray-200 p-6 text-center">
      <div className="mx-auto mb-2 flex h-12 w-12 items-center justify-center rounded-full bg-gray-100">
        <Search size={20} className="text-gray-400" />
      </div>
      <p className="text-sm font-medium text-gray-800">결과가 없어요</p>
      <p className="mt-1 text-xs text-gray-500">'{query}'에 대한 세션을 찾지 못했습니다.</p>
    </div>
  );
}
