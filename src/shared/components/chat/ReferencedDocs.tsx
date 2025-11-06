// src/shared/components/chat/ReferencedDocsPanel.tsx
import { useEffect, useMemo, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getReferencedDocuments } from '@/shared/api/chat.api';
import type { ReferencedDocument } from '@/shared/types/chat.types';
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
import Tooltip from '@/shared/components/Tooltip';
import clsx from 'clsx';

type Props = {
  sessionNo: string;
  messageNo: string;
  collapsedByDefault?: boolean;
};

const getIconByType = (type?: string) => {
  const t = (type || '').toLowerCase();
  if (['pdf', 'doc', 'docx', 'md', 'txt', 'rtf', 'xls', 'xlsx', 'csv', 'ppt', 'pptx'].includes(t)) {
    return <FileText size={16} className="text-gray-500" />;
  }
  return <File size={16} className="text-gray-500" />;
};

export default function ReferencedDocsPanel({
  sessionNo,
  messageNo,
  collapsedByDefault = false,
}: Props) {
  const [open, setOpen] = useState(!collapsedByDefault);
  const [hidden, setHidden] = useState(false);
  const lastCountRef = useRef<number>(0);

  const { data, isFetching, isError, refetch } = useQuery({
    queryKey: ['refDocs', sessionNo, messageNo],
    queryFn: async () => {
      const res = await getReferencedDocuments(sessionNo, messageNo);
      return (res.data.result?.data ?? []) as ReferencedDocument[];
    },
    enabled: open && !hidden,
    staleTime: 15_000,
  });

  useEffect(() => {
    if (Array.isArray(data)) lastCountRef.current = data.length;
  }, [data]);

  const docs = useMemo(() => {
    return (data ?? []) as ReferencedDocument[];
  }, [data]);

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
          }}
          className="inline-flex items-center gap-2 rounded-md border px-3 py-1.5 hover:bg-gray-50 hover:text-black"
        >
          <Eye size={14} />
          참조 문서 보기{typeof count === 'number' ? ` (${count})` : ''}
        </button>
      </div>
    );
  }

  return (
    <div className="mt-3 rounded-lg border bg-gray-50">
      <div className="w-full flex items-center justify-between px-3 py-2">
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
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
            <button onClick={() => setHidden(true)} className="rounded p-1 hover:bg-gray-100">
              <EyeOff size={16} className="text-gray-600" />
            </button>
          </Tooltip>
        </div>
      </div>

      {open && (
        <div className="px-3 pb-3">
          {isError ? (
            <div className="rounded-md border bg-white p-3 text-sm text-red-600">
              참조 문서를 불러오지 못했어요.
              <button onClick={() => refetch()} className="ml-2 underline">
                다시 시도
              </button>
            </div>
          ) : isFetching && !data ? (
            <div className="rounded-md border bg-white p-3 text-sm text-gray-500">불러오는 중…</div>
          ) : (
            <ul className="space-y-2">
              {docs.map((d) => {
                const title = d.title?.trim() || d.name || `문서 #${d.index}`;
                return (
                  <li
                    key={d.fileNo}
                    className="rounded-md border border-gray-200 bg-white px-3 py-2"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-start gap-2 min-w-0">
                        <div className="mt-0.5 shrink-0">{getIconByType(d.type)}</div>
                        <div className="min-w-0">
                          <div className="flex items-center gap-2">
                            <div className="line-clamp-1 text-sm font-medium text-gray-800">
                              {title}
                            </div>
                            {d.type ? (
                              <span className="shrink-0 rounded bg-gray-100 px-1.5 py-0.5 text-[10px] text-gray-500">
                                {d.type}
                              </span>
                            ) : null}
                            <span className="shrink-0 rounded bg-gray-100 px-1.5 py-0.5 text-[10px] text-gray-500">
                              #{d.index}
                            </span>
                          </div>
                          {d.snippet ? (
                            <p className="mt-1 line-clamp-2 text-xs text-gray-500">{d.snippet}</p>
                          ) : null}
                        </div>
                      </div>

                      <div className="flex shrink-0 items-center gap-1">
                        <Tooltip content="새 탭에서 열기" side="bottom">
                          <a
                            href={d.downloadUrl}
                            target="_blank"
                            rel="noreferrer"
                            className="rounded p-1 hover:bg-gray-100"
                          >
                            <ExternalLink size={16} className="text-gray-600" />
                          </a>
                        </Tooltip>

                        <Tooltip content="다운로드" side="bottom">
                          <a
                            href={d.downloadUrl}
                            download
                            className="rounded p-1 hover:bg-gray-100"
                          >
                            <Download size={16} className="text-gray-600" />
                          </a>
                        </Tooltip>
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
