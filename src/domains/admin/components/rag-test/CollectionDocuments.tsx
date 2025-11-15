import { useMemo, useState } from 'react';
import clsx from 'clsx';
import type { Collection } from '@/domains/admin/components/rag-test/types';
import { Upload, Download, Trash2, FileText, Folder, RefreshCw } from 'lucide-react';
import Checkbox from '@/shared/components/controls/Checkbox';
import Select from '@/shared/components/controls/Select';
import { fileTypeOptions } from '@/domains/admin/components/rag-settings/options';
import Tooltip from '@/shared/components/controls/Tooltip';

export type DocItem = {
  id: string;
  name: string;
  sizeKB: number;
  createdAt?: string;
  categoryNo?: string;
  type: string;
};

type Props = {
  collection: Collection;
  docs: DocItem[];
  onUpload?: (files: File[]) => void;
  onDownload?: (id: string) => void;
  onReindex?: (id: string) => void;
  onDelete?: (ids: string[]) => void;
  onRefresh?: () => void;
};

export default function CollectionDocuments({
  collection,
  docs,
  onUpload,
  onDownload,
  onDelete,
  onRefresh,
}: Props) {
  const [fileType, setFileType] = useState<'all' | DocItem['type']>('all');
  const [page, setPage] = useState(1);
  const pageSize = 5;

  const [selected, setSelected] = useState<Record<string, boolean>>({});

  const filtered = useMemo(
    () => docs.filter((d) => (fileType === 'all' ? true : d.type === fileType)),
    [docs, fileType]
  );

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const pageItems = filtered.slice((page - 1) * pageSize, page * pageSize);
  const selectedIds = Object.entries(selected)
    .filter(([, v]) => v)
    .map(([k]) => k);

  const toggleAll = (checked: boolean) => {
    const idsOnPage = pageItems.map((d) => d.id);
    setSelected((prev) => {
      const next = { ...prev };
      idsOnPage.forEach((id) => (next[id] = checked));
      return next;
    });
  };

  const handleFileInput: React.ChangeEventHandler<HTMLInputElement> = (e) => {
    const files = e.target.files ? Array.from(e.target.files) : [];
    if (files.length && onUpload) onUpload(files);
    e.currentTarget.value = '';
  };

  return (
    <div className="rounded-2xl border bg-white p-8 shadow-sm">
      <header className="mb-4 flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <h3 className="text-xl font-bold text-gray-900 mb-2 sm:mb-0">Collection 문서 목록</h3>
        <div className="flex items-center gap-2 flex-wrap">
          <Select
            value={fileType}
            onChange={(v) => {
              setFileType(v);
              setPage(1);
            }}
            options={fileTypeOptions}
            className="w-[120px]"
          />
          <label className="inline-flex cursor-pointer items-center gap-1.5 rounded-md border px-3 py-2 text-sm hover:bg-gray-50">
            <Upload size={16} />
            <span>문서 업로드</span>
            <input type="file" className="hidden" multiple onChange={handleFileInput} />
          </label>

          <button
            type="button"
            onClick={onRefresh}
            className={clsx(
              'flex items-center gap-1.5 text-sm rounded-md px-3 py-1',
              'border border-gray-200 text-gray-600 hover:bg-gray-50 hover:text-black transition-colors',
              'disabled:opacity-50 disabled:cursor-not-allowed'
            )}
          >
            <RefreshCw size={16} />
            {onRefresh ? '불러오는 중...' : '새로고침'}
          </button>
        </div>
      </header>

      <div className="flex items-center justify-between border border-gray-200 p-4 rounded-lg">
        <div className="flex items-center gap-4">
          <div className="flex p-4 items-center justify-center rounded-lg bg-[var(--color-hebees)] text-white">
            <Folder size={24} />
          </div>
          <span className="text-xl font-semibold text-gray-900">{collection.name}</span>
        </div>

        <div className="rounded-md bg-[var(--color-hebees)] px-4 py-2 text-sm font-medium text-white">
          {collection.ingestTemplate}
        </div>
      </div>

      <p className="mt-4 mb-2 inline-flex items-center gap-2 rounded-md bg-[var(--color-hebees-bg)] px-3 py-1 text-sm font-normal text-[var(--color-hebees)]">
        <span className="font-bold">TIP</span>
        선택한 문서만 업데이트/다운로드/삭제할 수 있어요.
      </p>

      <div className="mt-2 overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead>
            {/* <tr className="border-y bg-gray-50 text-gray-600"> */}
            <tr className="text-gray-600">
              <th className="w-10 px-4 py-2 text-left">
                <Checkbox
                  checked={pageItems.length > 0 && pageItems.every((d) => selected[d.id])}
                  indeterminate={
                    pageItems.some((d) => selected[d.id]) && !pageItems.every((d) => selected[d.id])
                  }
                  onChange={(e) => toggleAll(e.target.checked)}
                />
              </th>
              <th className="px-4 py-2 text-left">파일명</th>
              <th className="px-4 py-2 text-right">크기</th>
              <th className="px-4 py-2 text-right">벡터화 된 시간</th>
              <th className="px-4 py-2 text-right">카테고리</th>
              <th className="px-4 py-2 text-right">작업</th>
            </tr>
          </thead>
          <tbody>
            {pageItems.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-10 text-center text-gray-400">
                  등록된 문서가 없습니다.
                </td>
              </tr>
            )}

            {pageItems.map((doc) => (
              <tr key={doc.id} className="border-b last:border-b-0">
                <td className="px-4 py-2 align-middle">
                  <Checkbox
                    checked={!!selected[doc.id]}
                    onChange={(e) => setSelected((s) => ({ ...s, [doc.id]: e.target.checked }))}
                  />
                </td>
                <td className="px-4 py-2">
                  <div className="flex items-center gap-2">
                    <FileText size={16} className="text-[var(--color-hebees)]" />
                    <button className="truncate text-gray-800 hover:underline" title={doc.name}>
                      {doc.name}
                    </button>
                  </div>
                </td>
                <td className="px-4 py-2 text-right text-gray-600">{doc.sizeKB.toFixed(1)} KB</td>
                <td className="px-4 py-2 text-right text-gray-600">{doc.createdAt ?? '-'}</td>
                <td className="px-4 py-2 text-right">
                  <span className="inline-flex items-center rounded-md bg-gray-100 px-2 py-1 text-xs text-gray-700">
                    {doc.categoryNo ?? '없음'}
                  </span>
                </td>
                <td className="px-4 py-2">
                  <div className="flex items-center justify-end gap-1.5">
                    <Tooltip content="다운로드" side="top" offset={1}>
                      <button
                        className="rounded-md p-2 text-xs text-gray-700 hover:bg-gray-50"
                        onClick={() => onDownload?.(doc.id)}
                      >
                        <Download size={16} />
                      </button>
                    </Tooltip>
                    <Tooltip content="삭제" side="top" offset={1}>
                      <button
                        className="rounded-md p-2 text-xs text-red-600 hover:bg-red-50"
                        onClick={() => onDelete?.([doc.id])}
                      >
                        <Trash2 size={16} />
                      </button>
                    </Tooltip>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="text-sm text-[var(--color-hebees)] py-3">
        {selectedIds.length > 0 ? (
          <div className="flex items-center gap-2 rounded-md border border-[var(--color-hebees)] bg-[var(--color-hebees-bg)] px-3 py-2">
            <span>{selectedIds.length}개 파일이 선택되었습니다.</span>
          </div>
        ) : (
          <span className="text-gray-400">파일을 선택하면 일괄 작업을 수행할 수 있어요.</span>
        )}
      </div>

      <div className="flex items-center justify-center gap-5 text-sm py-3">
        <button
          onClick={() => setPage((p) => Math.max(1, p - 1))}
          disabled={page === 1}
          className="flex items-center gap-2 text-gray-700 disabled:text-gray-300"
        >
          <span className="text-lg">‹</span>
          <span className="hidden sm:inline">이전</span>
        </button>

        <div className="flex items-center gap-2 font-medium">
          {Array.from({ length: totalPages }).map((_, idx) => {
            const pageNum = idx + 1;
            return (
              <button
                key={pageNum}
                onClick={() => setPage(pageNum)}
                className={
                  page === pageNum ? 'text-black font-semibold' : 'text-gray-500 hover:text-black'
                }
              >
                {pageNum}
              </button>
            );
          })}
        </div>

        <button
          onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
          disabled={page === totalPages}
          className="flex items-center gap-1 text-gray-700 disabled:text-gray-300"
        >
          <span className="hidden sm:inline">다음</span>
          <span className="text-lg">›</span>
        </button>
      </div>
    </div>
  );
}
