import { useEffect, useMemo, useState } from 'react';
import { Download, Trash2, FileText, X } from 'lucide-react';
import Checkbox from '@/shared/components/Checkbox';
import Tooltip from '@/shared/components/Tooltip';
import Select from '@/shared/components/Select';
import Pagination from '@/shared/components/Pagination';
import { fileTypeOptions } from '@/domains/admin/components/rag-settings/options';
import { useCategoryStore } from '@/shared/store/categoryMap';

export type UploadedDoc = {
  id: string;
  name: string;
  sizeKB: number;
  uploadedAt?: string;
  category?: string;
  categoryId?: string;
  type: string;
  file?: File;
  fileNo?: string;
  status?: 'pending' | 'uploaded' | 'failed';
};

type Props = {
  docs: UploadedDoc[];
  pageSize?: number;
  onDownload?: (id: string) => void;
  onDelete?: (ids: string[]) => void;
  brand?: 'hebees' | 'retina';
  onSelectChange?: (ids: string[]) => void;
  hideFooter?: boolean;
};

export default function UploadedFileList({
  docs,
  pageSize = 5,
  onDownload,
  onDelete,
  brand = 'hebees',
  onSelectChange,
  hideFooter = false,
}: Props) {
  const [fileType, setFileType] = useState<'all' | UploadedDoc['type']>('all');
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<Record<string, boolean>>({});

  const categoryMap = useCategoryStore((s) => s.categoryMap);

  const filtered = useMemo(
    () => (fileType === 'all' ? docs : docs.filter((d) => d.type === fileType)),
    [docs, fileType]
  );

  const totalPages = useMemo(
    () => Math.max(1, Math.ceil(filtered.length / pageSize)),
    [filtered.length, pageSize]
  );
  const safePage = Math.min(page, totalPages);
  const pageItems = useMemo(
    () => filtered.slice((safePage - 1) * pageSize, safePage * pageSize),
    [filtered, safePage, pageSize]
  );

  const selectedIds = useMemo(() => Object.keys(selected).filter((id) => selected[id]), [selected]);

  useEffect(() => {
    onSelectChange?.(selectedIds);
  }, [selectedIds, onSelectChange]);

  useEffect(() => {
    if (!docs.length) {
      setSelected({});
      return;
    }
    setSelected((prev) => {
      const next: Record<string, boolean> = {};
      const existing = new Set(docs.map((d) => d.id));
      for (const id of Object.keys(prev)) {
        if (existing.has(id)) next[id] = prev[id];
      }
      return next;
    });

    setPage((p) =>
      Math.min(
        p,
        Math.max(1, Math.ceil((fileType === 'all' ? docs.length : filtered.length) / pageSize))
      )
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [docs, pageSize, fileType]);

  const toggleAll = (checked: boolean) => {
    const idsOnPage = pageItems.map((d) => d.id);
    setSelected((prev) => {
      const next = { ...prev };
      idsOnPage.forEach((id) => (next[id] = checked));
      return next;
    });
  };

  const brandBg =
    brand === 'hebees' ? 'bg-[var(--color-hebees-bg)]' : 'bg-[var(--color-retina-bg)]';
  const brandText =
    brand === 'hebees' ? 'text-[var(--color-hebees)]' : 'text-[var(--color-retina)]';
  const brandBorder =
    brand === 'hebees' ? 'border-[var(--color-hebees)]' : 'border-[var(--color-retina)]';

  return (
    <div className="mt-6 rounded-2xl border bg-white p-6">
      <div className="mb-4 flex flex-wrap items-center justify-end">
        <Select
          value={fileType}
          onChange={(v) => {
            setFileType(v);
            setPage(1);
          }}
          options={fileTypeOptions}
          className="w-[120px]"
        />
      </div>

      <div className="overflow-x-visible">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="text-gray-600">
              <th className="w-10 px-4 py-2 text-left">
                <Checkbox
                  checked={pageItems.length > 0 && pageItems.every((d) => selected[d.id])}
                  indeterminate={
                    pageItems.some((d) => selected[d.id]) && !pageItems.every((d) => selected[d.id])
                  }
                  brand={brand}
                  onChange={(e) => toggleAll(e.target.checked)}
                />
              </th>
              <th className="px-4 py-2 text-left">파일명</th>
              <th className="px-4 py-2 text-right">크기</th>
              <th className="px-4 py-2 text-right">업로드 시간</th>
              <th className="px-4 py-2 text-right">카테고리</th>
              <th className="px-4 py-2 text-right">작업</th>
            </tr>
          </thead>

          <tbody>
            {pageItems.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-10 text-center text-gray-400">
                  업로드된 파일이 없습니다.
                </td>
              </tr>
            ) : (
              pageItems.map((doc) => {
                const categoryName =
                  (doc.categoryId ? categoryMap[doc.categoryId] : undefined) ??
                  doc.category ??
                  '기타';

                return (
                  <tr key={doc.id} className="border-b last:border-b-0">
                    <td className="px-4 py-2">
                      <Checkbox
                        checked={!!selected[doc.id]}
                        onChange={(e) => setSelected((s) => ({ ...s, [doc.id]: e.target.checked }))}
                        brand={brand}
                      />
                    </td>

                    <td className="max-w-[200px] px-4 py-2 sm:max-w-[300px]">
                      <div className="min-w-0 flex items-center gap-2">
                        <div className="flex h-4 w-4 shrink-0 items-center justify-center">
                          <FileText size={16} className={brandText} />
                        </div>
                        <span className="min-w-0 flex-1">
                          <span className="block w-full truncate text-sm text-gray-800">
                            {doc.name}
                          </span>
                        </span>
                      </div>
                    </td>

                    <td className="px-4 py-2 text-right text-gray-600">
                      {doc.sizeKB >= 1024
                        ? `${(doc.sizeKB / 1024).toFixed(1)} MB`
                        : `${doc.sizeKB.toFixed(1)} KB`}
                    </td>

                    <td className="px-4 py-2 text-right text-gray-600">{doc.uploadedAt ?? '-'}</td>

                    <td className="px-4 py-2">
                      <div className="flex justify-end">
                        <span className="inline-flex items-center rounded-full border border-gray-300 px-3 py-1 text-xs text-gray-700">
                          {categoryName}
                        </span>
                      </div>
                    </td>

                    <td className="px-2 py-2">
                      <div className="flex items-center justify-end gap-1.5">
                        <Tooltip content="다운로드" side="top" offset={1}>
                          <button
                            className="rounded-md p-2 hover:bg-gray-50"
                            onClick={() => onDownload?.(doc.id)}
                          >
                            <Download size={16} />
                          </button>
                        </Tooltip>
                        <Tooltip content="삭제" side="top" offset={1}>
                          <button
                            className="rounded-md p-2 text-red-600 hover:bg-red-50"
                            onClick={() => onDelete?.([doc.id])}
                          >
                            <Trash2 size={16} />
                          </button>
                        </Tooltip>
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {!hideFooter && (
        <>
          <div className={`py-4 text-sm ${selectedIds.length ? brandText : 'text-gray-400'}`}>
            <div className={`py-4 text-sm ${selectedIds.length ? brandText : 'text-gray-400'}`}>
              {selectedIds.length ? (
                <div
                  className={`flex flex-wrap items-center justify-between gap-2 rounded-md border px-3 py-2 ${brandBorder} ${brandBg}`}
                >
                  <span>{selectedIds.length}개 파일이 선택되었습니다.</span>

                  <div className="flex items-center gap-1">
                    <Tooltip content="선택 해제" side="bottom">
                      <button
                        type="button"
                        onClick={() => setSelected({})}
                        className="rounded-md p-2 hover:bg-white text-black"
                      >
                        <X size={16} />
                      </button>
                    </Tooltip>

                    <Tooltip content="선택 다운로드" side="bottom">
                      <button
                        type="button"
                        onClick={() => {
                          selectedIds.forEach((id, i) => {
                            setTimeout(() => onDownload?.(id), i * 120);
                          });
                        }}
                        className="rounded-md p-2 hover:bg-white text-black"
                      >
                        <Download size={16} />
                      </button>
                    </Tooltip>

                    <Tooltip content="선택 삭제" side="bottom">
                      <button
                        type="button"
                        onClick={() => onDelete?.(selectedIds)}
                        className="rounded-md p-2 hover:bg-white text-red-600"
                      >
                        <Trash2 size={16} />
                      </button>
                    </Tooltip>
                  </div>
                </div>
              ) : (
                <span>파일을 선택하면 일괄 작업을 수행할 수 있어요.</span>
              )}
            </div>
          </div>

          <div className="flex items-center justify-center gap-5 py-3 text-sm">
            <Pagination pageNum={safePage} totalPages={totalPages} onPageChange={setPage} />
          </div>
        </>
      )}
    </div>
  );
}
