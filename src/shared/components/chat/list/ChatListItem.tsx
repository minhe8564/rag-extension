import { useEffect, useRef, useState } from 'react';
import { PencilLine, Trash2, Check, X, Loader2, Clock } from 'lucide-react';
import Tooltip from '@/shared/components/Tooltip';
import clsx from 'clsx';
import { toast } from 'react-toastify';
import type { SessionItem } from '@/shared/types/chat.types';
import { formatIsoDatetime } from '@/shared/utils/iso';

type Brand = 'retina' | 'hebees';

type Props = {
  session: SessionItem;
  isActive: boolean;
  onSelect: (s: SessionItem) => void;
  onRename: (title: string) => void;
  onRequestDelete: () => void;
  renaming?: boolean;
  deleting?: boolean;
  brand?: Brand;
};

const BRAND_THEME: Record<Brand, { primary: string; primaryBg: string }> = {
  retina: { primary: 'var(--color-retina)', primaryBg: 'var(--color-retina-bg)' },
  hebees: { primary: 'var(--color-hebees)', primaryBg: 'var(--color-hebees-bg)' },
};

export default function ChatListItem({
  session,
  isActive,
  onSelect,
  onRename,
  onRequestDelete,
  renaming,
  deleting,
  brand = 'retina',
}: Props) {
  const [editing, setEditing] = useState(false);
  const [title, setTitle] = useState(session.title || '');
  const inputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    if (editing) setTimeout(() => inputRef.current?.focus(), 0);
  }, [editing]);

  useEffect(() => {
    if (!editing) setTitle(session.title || '');
  }, [session.title, editing]);

  const submit = () => {
    const v = title.trim();
    if (!v) return toast.warn('제목을 입력해주세요.');
    onRename(v);
    setEditing(false);
  };

  const cancel = () => {
    setEditing(false);
    setTitle(session.title || '');
  };

  const cssVars: Record<`--${string}`, string> = {
    '--color-primary': BRAND_THEME[brand].primary,
    '--color-primary-bg': BRAND_THEME[brand].primaryBg,
  };

  return (
    <li
      data-active={isActive ? '1' : '0'}
      style={cssVars}
      className={clsx(
        'group flex items-center rounded-md gap-2 px-3 py-2',
        isActive ? 'bg-[var(--color-primary-bg)]' : 'hover:bg-gray-50'
      )}
    >
      <button onClick={() => onSelect(session)} className="flex-1 text-left" disabled={editing}>
        {editing ? (
          <div className="flex items-center gap-2">
            <input
              ref={inputRef}
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') submit();
                if (e.key === 'Escape') cancel();
              }}
              className="w-full rounded-md border px-2.5 py-1.5 text-sm border-gray-300 outline-none focus:outline-none focus:ring-0 focus:border-gray-400"
            />
          </div>
        ) : (
          <>
            <div className="line-clamp-1 mb-1 text-sm font-medium text-gray-800">
              {session.title || '제목 없음'}
            </div>
            <div className="inline-flex items-center text-xs text-gray-500 gap-1 transition-opacity">
              <Clock size={12} />
              {formatIsoDatetime(session.updatedAt || session.createdAt)}
            </div>
          </>
        )}
      </button>

      <div className="flex items-center gap-1">
        {editing ? (
          <>
            <Tooltip content="저장" side="bottom">
              <button
                onClick={submit}
                disabled={renaming}
                className="rounded-md p-1.5 text-[var(--color-primary)] hover:bg-white"
              >
                {renaming ? <Loader2 className="animate-spin" size={16} /> : <Check size={16} />}
              </button>
            </Tooltip>
            <Tooltip content="취소" side="bottom">
              <button onClick={cancel} className="rounded-md p-1.5 text-gray-500 hover:bg-white">
                <X size={16} />
              </button>
            </Tooltip>
          </>
        ) : (
          <>
            <Tooltip content="이름 변경" side="bottom">
              <button
                onClick={() => setEditing(true)}
                className="hidden rounded-md p-1.5 text-gray-500 hover:bg-white group-hover:block"
              >
                <PencilLine size={16} />
              </button>
            </Tooltip>
            <Tooltip content="삭제" side="bottom">
              <button
                onClick={onRequestDelete}
                className="hidden rounded-md p-1.5 text-red-500 hover:bg-white group-hover:block"
                disabled={!!deleting}
              >
                <Trash2 size={16} />
              </button>
            </Tooltip>
          </>
        )}
      </div>
    </li>
  );
}
