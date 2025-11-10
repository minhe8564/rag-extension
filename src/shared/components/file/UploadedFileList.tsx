import { useEffect, useMemo, useState } from 'react';
import { Download, Trash2, X } from 'lucide-react';
import Checkbox from '@/shared/components/Checkbox';
import Tooltip from '@/shared/components/Tooltip';
import Select from '@/shared/components/Select';
import Pagination from '@/shared/components/Pagination';
import { fileTypeOptions } from '@/domains/admin/components/rag-settings/options';
import { useCategoryStore } from '@/shared/store/categoryMap';
import ConflictBar from '@/shared/components/file/ConflictBar';
import FileNameCell from '@/shared/components/file/FileNameCell';
import { ensureUniqueName } from '@/shared/utils/fileName';

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
  onRename?: (id: string, nextName: string) => void;
  autoResolve?: 'none' | 'overwrite' | 'rename';
};

export default function UploadedFileList({
  docs,
  pageSize = 5,
  onDownload,
  onDelete,
  brand = 'hebees',
  onSelectChange,
  hideFooter = false,
  onRename,
  autoResolve = 'none',
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

  const nameGroups = useMemo(() => {
    const map = new Map<string, UploadedDoc[]>();
    filtered.forEach((d) => {
      const key = d.name.toLowerCase();
      const arr = map.get(key) ?? [];
      arr.push(d);
      map.set(key, arr);
    });

    const byRecent = (a: UploadedDoc, b: UploadedDoc) =>
      (new Date(b.uploadedAt || 0).getTime() || 0) - (new Date(a.uploadedAt || 0).getTime() || 0);

    map.forEach((arr) => arr.sort(byRecent));

    return map;
  }, [filtered]);

  const conflicts = useMemo(
    () => Array.from(nameGroups.values()).filter((arr) => arr.length > 1),
    [nameGroups]
  );

  // 자동 해결 정책 적용
  useEffect(() => {
    if (autoResolve === 'none' || filtered.length === 0 || !conflicts.length) return;

    const existing = new Set(docs.map((d) => d.name));
    if (autoResolve === 'overwrite') {
      const toDelete = conflicts.flatMap((group) => group.slice(1).map((d) => d.id));
      if (toDelete.length) onDelete?.(toDelete);
    } else if (autoResolve === 'rename') {
      conflicts.forEach((group) => {
        group.slice(1).forEach((d) => {
          if (!onRename) return;
          const next = ensureUniqueName(d.name, existing);
          existing.add(next);
          onRename(d.id, next);
        });
      });
    }
  }, [autoResolve, conflicts, filtered.length, docs, onDelete, onRename]);

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

  const isLoser = (doc: UploadedDoc): boolean => {
    const arr = nameGroups.get(doc.name.toLowerCase());
    return !!(arr && arr.length > 1 && arr[0].id !== doc.id);
  };

  // 일괄 처리 핸들러
  const resolveAllOverwrite = () => {
    const toDelete = conflicts.flatMap((group) => group.slice(1).map((d) => d.id));
    if (toDelete.length) onDelete?.(toDelete);
  };
  const resolveAllRename = () => {
    if (!onRename) return;
    const existing = new Set(docs.map((d) => d.name));
    conflicts.forEach((group) => {
      group.slice(1).forEach((d) => {
        const next = ensureUniqueName(d.name, existing);
        existing.add(next);
        onRename(d.id, next);
      });
    });
  };

  return (
    <div className="mt-6 rounded-2xl border bg-white p-6">
      <ConflictBar
        hidden={autoResolve !== 'none'}
        conflictCount={conflicts.length}
        onOverwriteAll={resolveAllOverwrite}
        onRenameAll={resolveAllRename}
      />

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

                const losing = isLoser(doc);

                const existingNames = docs.filter((d) => d.id !== doc.id).map((d) => d.name);

                return (
                  <tr
                    key={doc.id}
                    className={`border-b last:border-b-0 ${losing ? 'bg-amber-50/40' : ''}`}
                  >
                    <td className="px-4 py-2">
                      <Checkbox
                        checked={!!selected[doc.id]}
                        onChange={(e) => setSelected((s) => ({ ...s, [doc.id]: e.target.checked }))}
                        brand={brand}
                      />
                    </td>

                    <td className="max-w-[260px] px-4 py-2 sm:max-w-[360px]">
                      <FileNameCell
                        id={doc.id}
                        name={doc.name}
                        losing={losing}
                        brandTextClass={brandText}
                        onRename={onRename}
                        existingNames={existingNames}
                      />
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
                        {losing && (
                          <Tooltip
                            content="이 항목만 삭제하여 최신만 남기기"
                            side="bottom"
                            offset={1}
                          >
                            <button
                              className="rounded-md p-2 text-red-600 hover:bg-red-50"
                              onClick={() => onDelete?.([doc.id])}
                            >
                              <Trash2 size={16} />
                            </button>
                          </Tooltip>
                        )}
                        <Tooltip content="다운로드" side="bottom" offset={1}>
                          <button
                            className="rounded-md p-2 hover:bg-gray-50"
                            onClick={() => onDownload?.(doc.id)}
                          >
                            <Download size={16} />
                          </button>
                        </Tooltip>

                        {!losing && (
                          <Tooltip content="삭제" side="bottom" offset={1}>
                            <button
                              className="rounded-md p-2 text-red-600 hover:bg-red-50"
                              onClick={() => onDelete?.([doc.id])}
                            >
                              <Trash2 size={16} />
                            </button>
                          </Tooltip>
                        )}
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

          <div className="flex items-center justify-center gap-5 py-3 text-sm">
            <Pagination pageNum={safePage} totalPages={totalPages} onPageChange={setPage} />
          </div>
        </>
      )}
    </div>
  );
}
