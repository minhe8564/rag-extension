import { useEffect, useMemo, useRef, useState } from 'react';
import { ChevronDown, Plus, X, Trash2 } from 'lucide-react';

export type CategoryOption = { label: string; value: string; color?: string };

type Props = {
  value?: string;
  options: CategoryOption[];
  onChange: (value: string) => void;
  onCreate?: (name: string) => void;
  onDeleteOption?: (value: string) => void;
  placeholder?: string;
  className?: string;
  disabled?: boolean;
};

export default function CategorySelect({
  value,
  options,
  onChange,
  onCreate,
  onDeleteOption,
  placeholder = '카테고리 선택',
  className = '',
  disabled,
}: Props) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const rootRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (!rootRef.current) return;
      if (!rootRef.current.contains(e.target as Node)) setOpen(false);
    };
    if (open) document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [open]);

  useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 0);
    } else {
      setQuery('');
    }
  }, [open]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return options;
    return options.filter(o => o.label.toLowerCase().includes(q));
  }, [query, options]);

  const existsExact = useMemo(() => {
    const q = query.trim();
    return q.length > 0 && options.some(o => o.label === q || o.value === q);
  }, [query, options]);

  const current = options.find(o => o.value === value);

  const select = (v: string) => {
    onChange(v);
    setOpen(false);
  };

  const createAndSelect = (name: string) => {
    const clean = name.trim();
    if (!clean) return;
    onCreate?.(clean);
    onChange(clean);
    setOpen(false);
    setQuery('');
  };

  return (
    <div ref={rootRef} className={`relative inline-flex ${className}`}>
      <button
        type="button"
        disabled={disabled}
        onClick={() => setOpen(o => !o)}
        className={`group inline-flex max-w-[220px] items-center gap-1 rounded-md border px-2.5 py-1.5 text-xs
                    ${disabled ? 'cursor-not-allowed bg-gray-50 text-gray-400' : 'hover:bg-gray-50'} `}
      >
        {current ? (
          <span className="inline-flex items-center gap-1 truncate">
            <span
              className="inline-block h-2 w-2 rounded-full"
              style={{ background: current.color ?? 'var(--color-hebees)' }}
            />
            <span className="truncate">{current.label}</span>
          </span>
        ) : (
          <span className="text-gray-400">{placeholder}</span>
        )}
        {value && !disabled && (
          <span
            onClick={e => {
              e.stopPropagation();
              onChange('');
            }}
            className="ml-0.5 hidden rounded p-0.5 text-gray-400 hover:bg-gray-100 hover:text-gray-600 group-hover:inline-block"
            title="지우기"
          >
            <X className="size-3.5" />
          </span>
        )}
        <ChevronDown className="ml-0.5 size-3.5 text-gray-400" />
      </button>

      {open && (
        <div
          className="absolute z-50 mt-9 w-[260px] overflow-hidden rounded-lg border bg-white shadow-xl"
          role="listbox"
        >
          <div className="border-b bg-white p-2">
            <input
              ref={inputRef}
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter') {
                  if (filtered.length > 0 && query.trim().length === 0) {
                    select(filtered[0].value);
                  } else if (filtered.length > 0 && query.trim().length > 0 && existsExact) {
                    select(filtered[0].value);
                  } else if (!existsExact && query.trim().length > 0) {
                    createAndSelect(query);
                  }
                }
                if (e.key === 'Escape') setOpen(false);
              }}
              placeholder="검색 또는 새로 만들기…"
              className="w-full rounded-md border border-gray-200 px-2 py-1.5 text-xs
           focus:outline-none focus:ring-0 focus:border-gray-200 bg-white"
            />
          </div>

          <div className="max-h-64 overflow-auto p-1">
            {filtered.map(o => (
              <div
                key={o.value}
                onClick={() => select(o.value)}
                className={`group flex cursor-pointer items-center justify-between rounded-md px-2 py-1.5 text-sm hover:bg-gray-50
                            ${o.value === value ? 'bg-gray-50' : ''}`}
              >
                <span className="inline-flex items-center gap-2 truncate">
                  <span
                    className="inline-block h-2 w-2 shrink-0 rounded-full"
                    style={{ background: o.color ?? 'var(--color-hebees)' }}
                  />
                  <span className="truncate">{o.label}</span>
                </span>

                {!!onDeleteOption && (
                  <button
                    title="옵션 삭제"
                    onClick={e => {
                      e.stopPropagation();
                      onDeleteOption(o.value);
                    }}
                    className="invisible rounded p-1 text-gray-400 hover:bg-red-50 hover:text-red-600 group-hover:visible"
                  >
                    <Trash2 className="size-4" />
                  </button>
                )}
              </div>
            ))}

            {!existsExact && query.trim().length > 0 && (
              <button
                onClick={() => createAndSelect(query)}
                className="mt-1 flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm text-gray-700 hover:bg-gray-50"
              >
                <Plus className="size-4" />
                <span className="truncate">
                  <strong className="font-medium">“{query.trim()}”</strong> 새 카테고리 만들기
                </span>
              </button>
            )}

            {filtered.length === 0 && query.trim().length === 0 && (
              <div className="px-2 py-3 text-xs text-gray-400">카테고리가 없습니다.</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
