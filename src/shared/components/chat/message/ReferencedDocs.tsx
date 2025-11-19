import { useEffect, useMemo, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getReferencedDocuments } from '@/shared/api/chat.api';
import type { ReferencedDocument } from '@/shared/types/chat.types';
import ChatMarkdown from '@/shared/components/chat/message/ChatMarkdown';
import {
  FileText,
  File,
  FileSearch,
  ExternalLink,
  Download,
  EyeOff,
  ChevronDown,
  Eye,
} from 'lucide-react';
import Tooltip from '@/shared/components/controls/Tooltip';
import clsx from 'clsx';
import { Loader2 } from 'lucide-react';
import { useReferencedDocsStore } from '@/shared/store/useReferencedDocsStore';

type Props = {
  sessionNo?: string;
  messageNo?: string;
  collapsedByDefault?: boolean;
  references?: ReferencedDocument[];
};

const getFileMeta = (type?: string) => {
  const t = (type || '').toLowerCase();

  let icon = <FileText size={16} className="text-gray-500" />;
  let chipLabel = t ? t.toUpperCase() : '';
  let chipClass = 'border-gray-200 bg-gray-50 text-gray-600';

  if (t === 'pdf') {
    icon = <FileText size={16} className="text-emerald-500" />;
    chipLabel = 'PDF';
    chipClass = 'border-emerald-100 bg-emerald-50 text-emerald-700';
  } else if (t === 'png') {
    icon = <File size={16} className="text-amber-500" />;
    chipLabel = 'PNG';
    chipClass = 'border-amber-100 bg-amber-50 text-amber-700';
  }
  return { icon, chipLabel, chipClass };
};

export default function ReferencedDocsPanel({
  sessionNo,
  messageNo,
  collapsedByDefault = false,
  references,
}: Props) {
  const { getState, setState } = useReferencedDocsStore();
  const storedState = messageNo ? getState(messageNo) : undefined;

  const hasInlineReferences = Array.isArray(references) && references.length > 0;

  const getInitialOpenState = (): boolean => {
    if (storedState?.open !== undefined) return storedState.open;
    return !collapsedByDefault;
  };

  const [open, setOpen] = useState(() => getInitialOpenState());
  const [hidden, setHidden] = useState(() => storedState?.hidden ?? false);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [activeType, setActiveType] = useState<'all' | string>('all');
  const lastCountRef = useRef<number>(0);

  useEffect(() => {
    if (messageNo) {
      const state = getState(messageNo);
      if (state) {
        setHidden(state.hidden);
        if (state.open !== undefined) {
          setOpen(state.open);
        }
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [messageNo]);

  const { data, isFetching, isError, refetch } = useQuery({
    queryKey: ['refDocs', sessionNo, messageNo],
    queryFn: async () => {
      const res = await getReferencedDocuments(sessionNo!, messageNo!);
      return (res.data.result?.data ?? []) as ReferencedDocument[];
    },
    enabled:
      !hasInlineReferences &&
      open &&
      !hidden &&
      !!sessionNo &&
      !!messageNo &&
      messageNo !== '__pending__',
    staleTime: 15_000,
  });

  useEffect(() => {
    if (!hasInlineReferences && Array.isArray(data)) {
      lastCountRef.current = data.length;
    }
  }, [data, hasInlineReferences]);

  const docs = useMemo(() => {
    if (hasInlineReferences) return (references ?? []) as ReferencedDocument[];
    return (data ?? []) as ReferencedDocument[];
  }, [hasInlineReferences, references, data]);

  const availableTypes = useMemo(() => {
    const set = new Set<string>();
    docs.forEach((d) => {
      if (d.type) {
        set.add(d.type.toLowerCase());
      }
    });
    return Array.from(set);
  }, [docs]);

  const filteredDocs = useMemo(() => {
    if (activeType === 'all') return docs;
    return docs.filter((d) => (d.type || '').toLowerCase() === activeType);
  }, [docs, activeType]);

  if (docs.length === 0) {
    return null;
  }

  if (hidden) {
    const count = docs.length || lastCountRef.current;
    return (
      <div className="mt-2 text-gray-500 text-xs">
        <button
          onClick={() => {
            setHidden(false);
            setOpen(true);
            if (messageNo) {
              setState(messageNo, { hidden: false, open: true });
            }
          }}
          className="inline-flex items-center gap-2 rounded-md border px-3 py-1.5 hover:bg-gray-50 hover:text-black"
        >
          <Eye size={14} />
          참조 문서 보기{typeof count === 'number' ? ` (${count})` : ''}
        </button>
      </div>
    );
  }

  const truncateByChars = (text: string, max: number) => {
    if (!text) return '';
    return text.length > max ? text.slice(0, max) + '…' : text;
  };

  return (
    <div className="mt-3 rounded-lg border bg-gray-50">
      <div className="w-full flex items-center justify-between px-3 py-2">
        <button
          type="button"
          onClick={() => {
            setOpen((v) => {
              const newValue = !v;
              if (messageNo) {
                setState(messageNo, { open: newValue });
              }
              return newValue;
            });
          }}
          className="inline-flex items-center gap-2 text-sm font-medium text-gray-700"
          aria-expanded={open}
        >
          <FileSearch size={16} className="text-gray-500" />
          참조 문서
          <span className="text-gray-400">({docs.length})</span>
          <ChevronDown
            size={16}
            className={clsx(
              'text-gray-500 transition-transform duration-200',
              open ? 'rotate-0' : '-rotate-90'
            )}
          />
        </button>

        <div className="flex items-center gap-1">
          <Tooltip content="참조 문서 숨기기" side="bottom">
            <button
              onClick={() => {
                setHidden(true);
                if (messageNo) {
                  setState(messageNo, { hidden: true });
                }
              }}
              className="rounded p-1 hover:bg-gray-100"
            >
              <EyeOff size={16} className="text-gray-600" />
            </button>
          </Tooltip>
        </div>
      </div>

      {open && (
        <div className="px-3 pb-3">
          {availableTypes.length > 0 && (
            <div className="mb-2 flex items-center gap-1 overflow-x-auto pb-1 -mx-1 px-1">
              <button
                type="button"
                onClick={() => setActiveType('all')}
                className={clsx(
                  'inline-flex items-center rounded-full border px-2.5 py-1 text-[11px] font-medium whitespace-nowrap transition-colors',
                  activeType === 'all'
                    ? 'border-gray-300 bg-white text-gray-900 shadow-sm'
                    : 'border-gray-200 bg-gray-50 text-gray-600 hover:bg-white'
                )}
              >
                전체
                <span className="ml-1 text-[10px] text-gray-400">({docs.length})</span>
              </button>

              {availableTypes.map((t) => {
                const { chipLabel, chipClass } = getFileMeta(t);
                const isActive = activeType === t;
                return (
                  <button
                    key={t}
                    type="button"
                    onClick={() => setActiveType((prev) => (prev === t ? 'all' : t))}
                    className={clsx(
                      'inline-flex items-center rounded-full border px-2.5 py-1 text-[11px] font-medium whitespace-nowrap transition-colors',
                      chipClass,
                      isActive
                        ? 'ring-1 ring-offset-1 ring-gray-300'
                        : 'opacity-80 hover:opacity-100'
                    )}
                  >
                    <span className="mr-1 h-1.5 w-1.5 rounded-full bg-current" />
                    {chipLabel}
                  </button>
                );
              })}
            </div>
          )}

          {!hasInlineReferences && isError ? (
            <div className="rounded-md border bg-white p-3 text-sm text-red-600">
              참조 문서를 불러오지 못했어요.
              <button onClick={() => refetch()} className="ml-2 underline">
                다시 시도
              </button>
            </div>
          ) : !hasInlineReferences && isFetching && !data ? (
            <div className="flex items-center justify-center py-8 text-gray-500">
              <Loader2 size={18} className="mr-2 animate-spin" />
              불러오는 중…
            </div>
          ) : (
            <ul className="space-y-2">
              {filteredDocs.map((d, idx) => {
                const title = d.title?.trim() || d.name || `문서 #${d.index}`;
                const docKey = `${d.fileNo ?? 'nofile'}-${d.index ?? idx}-${idx}`;
                const isExpanded = expandedId === docKey;
                const { icon, chipLabel, chipClass } = getFileMeta(d.type);

                return (
                  <li
                    key={docKey}
                    className={clsx(
                      'rounded-md border border-gray-200 bg-white px-3 py-2',
                      isExpanded && 'px-4 py-3'
                    )}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-start gap-2 min-w-0">
                        <div className="mt-0.5 shrink-0">{icon}</div>
                        <div className="min-w-0">
                          <div className="mb-3 flex items-center gap-2">
                            <div className="line-clamp-1 text-sm font-medium text-gray-800">
                              {title}
                            </div>
                            {d.type && (
                              <span
                                className={clsx(
                                  'shrink-0 inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium border',
                                  chipClass
                                )}
                              >
                                <span className="mr-1 h-1.5 w-1.5 rounded-full bg-current" />
                                {chipLabel}
                              </span>
                            )}
                          </div>

                          {d.snippet && (
                            <div
                              className={clsx(
                                'mt-2 transition-all',
                                isExpanded &&
                                  'relative rounded-lg border border-gray-200 bg-white px-5 py-5'
                              )}
                            >
                              {isExpanded && (
                                <div className="mb-3 flex items-center justify-between gap-10">
                                  <div className="text-xs font-semibold uppercase tracking-wide text-gray-500">
                                    문서 미리보기
                                  </div>
                                  <div className="text-[11px] text-gray-700 bg-gray-100 px-2.5 py-1 rounded-full border border-gray-200 shadow-sm">
                                    텍스트를 드래그하면 하이라이트해서 볼 수 있어요
                                  </div>
                                </div>
                              )}

                              {isExpanded ? (
                                <ChatMarkdown>{d.snippet}</ChatMarkdown>
                              ) : (
                                <p className="text-gray-500 text-xs">
                                  {truncateByChars(d.snippet, 90)}
                                </p>
                              )}
                            </div>
                          )}
                        </div>
                      </div>

                      <div className="flex shrink-0 items-center gap-1">
                        {d.snippet && (
                          <Tooltip content={isExpanded ? '접기' : '전체 보기'} side="bottom">
                            <button
                              type="button"
                              onClick={() =>
                                setExpandedId((prev) => (prev === docKey ? null : docKey))
                              }
                              className="rounded p-1 hover:bg-gray-100"
                            >
                              <ExternalLink size={16} className="text-gray-600" />
                            </button>
                          </Tooltip>
                        )}

                        {d.downloadUrl && (
                          <Tooltip content="다운로드" side="bottom">
                            <a
                              href={d.downloadUrl}
                              download
                              className="rounded p-1 hover:bg-gray-100"
                            >
                              <Download size={16} className="text-gray-600" />
                            </a>
                          </Tooltip>
                        )}
                      </div>
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
