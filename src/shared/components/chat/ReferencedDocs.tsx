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
  Link as LinkIcon,
  Download,
  Trash2,
  Copy,
  ChevronDown,
  RotateCw,
  Eye,
} from 'lucide-react';
import Tooltip from '@/shared/components/Tooltip';
import clsx from 'clsx';
import { toast } from 'react-toastify';

type Props = {
  sessionNo: string;
  messageNo: string;
  collapsedByDefault?: boolean;
  className?: string;
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
  className,
}: Props) {
  const [open, setOpen] = useState(!collapsedByDefault);
  const [hidden, setHidden] = useState(false); // 패널 자체 숨김
  const [removedIds, setRemovedIds] = useState<Set<string>>(new Set()); // 문서별 숨김
  const lastCountRef = useRef<number>(0); // 숨김 상태에서도 N 표시용

  const { data, isFetching, isError, refetch } = useQuery({
    queryKey: ['refDocs', sessionNo, messageNo],
    queryFn: async () => {
      const res = await getReferencedDocuments(sessionNo, messageNo);
      return (res.data.result?.data ?? []) as ReferencedDocument[];
    },
    enabled: open && !hidden, // 열렸을 때만 로딩
    staleTime: 15_000,
  });

  // 최신 카운트 저장 (숨김 상태에서 배지용)
  useEffect(() => {
    if (Array.isArray(data)) lastCountRef.current = data.length;
  }, [data]);

  const docs = useMemo(() => {
    const raw = (data ?? []) as ReferencedDocument[];
    const filtered = raw.filter((d) => !removedIds.has(d.fileNo));
    return filtered.sort((a, b) => a.index - b.index);
  }, [data, removedIds]);

  // 숨겨진 상태라면 "참조 문서 보기 (N)" 버튼만 노출
  if (hidden) {
    const count = docs.length || lastCountRef.current;
    return (
      <div className={clsx('mt-2', className)}>
        <button
          onClick={() => {
            setHidden(false);
            setOpen(true);
          }}
          className="inline-flex items-center gap-2 rounded-md border px-3 py-1.5 text-sm hover:bg-gray-50"
        >
          <Eye size={16} />
          참조 문서 보기{typeof count === 'number' ? ` (${count})` : ''}
        </button>
      </div>
    );
  }

  return (
    <div className={clsx('mt-3 rounded-lg border bg-gray-50', className)}>
      {/* Header */}
      <div className="w-full flex items-center justify-between px-3 py-2">
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          className="inline-flex items-center gap-2 text-sm font-medium text-gray-700"
          aria-expanded={open}
        >
          <FileSearch size={16} className="text-gray-500" />
          참조 문서
          <span className="text-gray-400">
            ({docs.length}
            {isFetching ? '…' : ''})
          </span>
          <ChevronDown
            size={16}
            className={clsx(
              'text-gray-500 transition-transform duration-200',
              open ? 'rotate-0' : '-rotate-90'
            )}
          />
        </button>

        <div className="flex items-center gap-1">
          <Tooltip content="새로고침" side="bottom">
            <button
              onClick={() => refetch()}
              disabled={isFetching}
              className="rounded p-1 hover:bg-gray-100 disabled:opacity-60"
            >
              <RotateCw size={16} className={clsx('text-gray-600', isFetching && 'animate-spin')} />
            </button>
          </Tooltip>

          <Tooltip content="패널 숨기기" side="bottom">
            <button onClick={() => setHidden(true)} className="rounded p-1 hover:bg-gray-100">
              <Trash2 size={16} className="text-gray-600" />
            </button>
          </Tooltip>
        </div>
      </div>

      {/* Body */}
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
          ) : docs.length === 0 ? (
            <div className="rounded-md border bg-white p-3 text-sm text-gray-500">
              표시할 참조 문서가 없어요.
            </div>
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
                            aria-label="open"
                          >
                            <ExternalLink size={16} className="text-gray-600" />
                          </a>
                        </Tooltip>

                        <Tooltip content="URL 복사" side="bottom">
                          <button
                            onClick={() => {
                              navigator.clipboard.writeText(d.downloadUrl);
                              toast.success('URL을 복사했어요.');
                            }}
                            className="rounded p-1 hover:bg-gray-100"
                            aria-label="copy url"
                          >
                            <LinkIcon size={16} className="text-gray-600" />
                          </button>
                        </Tooltip>

                        <Tooltip content="제목 복사" side="bottom">
                          <button
                            onClick={() => {
                              navigator.clipboard.writeText(title);
                              toast.success('제목을 복사했어요.');
                            }}
                            className="rounded p-1 hover:bg-gray-100"
                            aria-label="copy title"
                          >
                            <Copy size={16} className="text-gray-600" />
                          </button>
                        </Tooltip>

                        <Tooltip content="이 항목 숨기기" side="bottom">
                          <button
                            onClick={() => {
                              setRemovedIds((prev) => new Set(prev).add(d.fileNo));
                              toast.success('목록에서 숨겼어요.');
                            }}
                            className="rounded p-1 hover:bg-gray-100"
                            aria-label="remove"
                          >
                            <Trash2 size={16} className="text-gray-600" />
                          </button>
                        </Tooltip>

                        <Tooltip content="다운로드" side="bottom">
                          <a
                            href={d.downloadUrl}
                            download
                            className="rounded p-1 hover:bg-gray-100"
                            aria-label="download"
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
