import { useEffect, useState } from 'react';
import clsx from 'clsx';
import { Pencil, Trash2, Plus } from 'lucide-react';
import Tooltip from '@/shared/components/Tooltip';
import { getIngestTemplates } from '@/domains/admin/api/rag-settings/ingest-templates.api';
import { getQueryTemplates } from '@/domains/admin/api/rag-settings/query-templates.api';

type Props = {
  kind: 'ingest' | 'query';
  active: string;
  onSelect: (id: string) => void;
  className?: string;
  onEdit?: (id: string) => void;
  onDelete?: (id: string) => void;
  onCreate?: () => void;
};

type IngestItem = { ingestNo: string; name: string; isDefault: boolean };
type QueryItem = { queryNo: string; name: string; isDefault: boolean };

function isIngestItem(x: IngestItem | QueryItem): x is IngestItem {
  return typeof (x as IngestItem).ingestNo === 'string';
}

export default function TemplateList({
  kind,
  active,
  onSelect,
  className,
  onEdit,
  onDelete,
  onCreate,
}: Props) {
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [items, setItems] = useState<Array<IngestItem | QueryItem>>([]);

  useEffect(() => {
    const run = async () => {
      try {
        setLoading(true);
        setErr(null);
        if (kind === 'ingest') {
          const res = await getIngestTemplates({ pageNum: 1, pageSize: 100 });
          setItems(res.data ?? []);
        } else {
          const res = await getQueryTemplates({ pageNum: 1, pageSize: 100 });
          setItems(res.data ?? []);
        }
      } catch {
        setErr('템플릿 목록을 불러오지 못했어요.');
      } finally {
        setLoading(false);
      }
    };
    run();
  }, [kind]);

  return (
    <aside
      className={clsx('rounded-2xl border bg-white p-4 shadow-sm', 'border-gray-200', className)}
    >
      <div className="mb-3 flex items-center justify-between">
        <div className="text-sm font-semibold text-gray-700">
          {kind === 'ingest' ? 'Ingest 템플릿' : 'Query 템플릿'}
        </div>
        {onCreate && (
          <button
            type="button"
            onClick={() => {
              setItems((prev) => prev.map((t) => ({ ...t, isDefault: false })));
              onCreate();
            }}
            className={clsx(
              'inline-flex items-center gap-1 rounded-lg px-2.5 py-1 text-xs font-medium transition-colors',
              'border border-[var(--color-hebees)] text-[var(--color-hebees)]',
              'hover:bg-[var(--color-hebees-bg)]',
              'focus:outline-none focus:ring-0'
            )}
          >
            <Plus size={14} /> 새 템플릿
          </button>
        )}
      </div>

      {loading ? (
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-10 w-full animate-pulse rounded-xl bg-gray-100" />
          ))}
        </div>
      ) : err ? (
        <div className="rounded-md bg-amber-50 p-3 text-sm text-amber-700">{err}</div>
      ) : items.length === 0 ? (
        <div className="text-sm text-gray-500">템플릿이 없습니다.</div>
      ) : (
        <ul className="space-y-3">
          {items.map((t) => {
            const id = isIngestItem(t) ? t.ingestNo : t.queryNo;
            const name = t.name;
            const isActive = id === active;
            const isDefault = t.isDefault === true;

            return (
              <li key={id} className="group">
                <div
                  className={clsx(
                    'flex items-center justify-between rounded-xl px-3 py-2 transition border',
                    isActive
                      ? 'border-[var(--color-hebees)] bg-[var(--color-hebees-bg)]'
                      : 'border-gray-200 bg-white hover:bg-gray-50'
                  )}
                >
                  <button
                    type="button"
                    onClick={() => onSelect(id)}
                    className="min-w-0 grow text-left outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-hebees)]/40 rounded-md"
                    aria-pressed={isActive}
                  >
                    <div
                      className={`line-clamp-1 text-sm font-medium ${
                        isActive ? 'text-[var(--color-hebees)]' : ''
                      }`}
                    >
                      {name}
                    </div>
                    {isDefault && (
                      <span className="mt-1 inline-flex items-center rounded bg-white px-1.5 py-[1px] text-[10px] font-medium text-gray-600">
                        기본
                      </span>
                    )}
                  </button>

                  <div
                    className={clsx(
                      'ml-2 shrink-0 flex items-center gap-2 transition-opacity',
                      isActive
                        ? 'opacity-100'
                        : 'opacity-0 group-hover:opacity-100 group-focus-within:opacity-100'
                    )}
                  >
                    {onEdit && (
                      <Tooltip content="편집" side="bottom">
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            onEdit(id);
                          }}
                          className={clsx(
                            'h-9 w-9 rounded-lg border bg-white',
                            'inline-flex items-center justify-center',
                            'border-gray-200 hover:bg-gray-100',
                            'focus:outline-none '
                          )}
                        >
                          <Pencil size={16} strokeWidth={2} className="text-gray-700" />
                        </button>
                      </Tooltip>
                    )}
                    {onDelete && (
                      <Tooltip content="삭제" side="bottom">
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            onDelete(id);
                          }}
                          className={clsx(
                            'h-9 w-9 rounded-lg border bg-white',
                            'inline-flex items-center justify-center',
                            'border-gray-200 hover:bg-gray-100',
                            'focus:outline-none'
                          )}
                        >
                          <Trash2 size={16} strokeWidth={2} className="text-gray-700" />
                        </button>
                      </Tooltip>
                    )}
                  </div>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </aside>
  );
}
