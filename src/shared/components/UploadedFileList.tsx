import { useMemo, useState } from 'react';
import { Download, Trash2, FileText } from 'lucide-react';
import Checkbox from '@/shared/components/Checkbox';
import Tooltip from '@/shared/components/Tooltip';
import CategorySelect from '@/shared/components/CategorySelect';
import type { CategoryOption } from '@/shared/components/CategorySelect';
import Select from '@/shared/components/Select';
import Pagination from '@/shared/components/Pagination';
import { fileTypeOptions } from '@/domains/admin/components/rag-settings/options';

export type UploadedDoc = {
  id: string;
  name: string;
  sizeKB: number;
  uploadedAt?: string;
  category?: string;
  type: 'pdf' | 'docx' | 'pptx' | 'xlsx' | 'txt' | 'image';
  file?: File;
};

type Props = {
  docs: UploadedDoc[];
  pageSize?: number;
  onDownload?: (id: string) => void;
  onDelete?: (ids: string[]) => void;
  onCategoryChange?: (id: string, category: string) => void;
  brand?: 'hebees' | 'retina';
};

export default function UploadedFileList({
  docs,
  pageSize = 5,
  onDownload,
  onDelete,
  onCategoryChange,
  brand = 'hebees',
}: Props) {
  const [fileType, setFileType] = useState<'all' | UploadedDoc['type']>('all');
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<Record<string, boolean>>({});

  const defaultCats = ['업무 매뉴얼', '정책/규정', '개발 문서', '기타'];
  const initialSet = new Set<string>([
    ...defaultCats,
    ...docs.map(d => d.category).filter((v): v is string => !!v),
  ]);
  const [categoryOptions, setCategoryOptions] = useState<CategoryOption[]>(
    Array.from(initialSet).map(v => ({ label: v, value: v }))
  );

  const addCategory = (name: string) => {
    setCategoryOptions(prev =>
      prev.some(o => o.value === name) ? prev : [...prev, { label: name, value: name }]
    );
  };
  const removeCategory = (value: string) =>
    setCategoryOptions(prev => prev.filter(o => o.value !== value));

  const filtered = useMemo(
    () => (fileType === 'all' ? docs : docs.filter(d => d.type === fileType)),
    [docs, fileType]
  );

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const pageItems = filtered.slice((page - 1) * pageSize, page * pageSize);
  const selectedIds = Object.keys(selected).filter(id => selected[id]);

  const toggleAll = (checked: boolean) => {
    const idsOnPage = pageItems.map(d => d.id);
    setSelected(prev => {
      const next = { ...prev };
      idsOnPage.forEach(id => (next[id] = checked));
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
      <div className="flex items-center justify-end mb-4 flex-wrap">
        <Select
          value={fileType}
          onChange={v => {
            setFileType(v as any);
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
                  checked={pageItems.length > 0 && pageItems.every(d => selected[d.id])}
                  indeterminate={
                    pageItems.some(d => selected[d.id]) && !pageItems.every(d => selected[d.id])
                  }
                  onChange={e => toggleAll(e.target.checked)}
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
              pageItems.map(doc => (
                <tr key={doc.id} className="border-b last:border-b-0">
                  <td className="px-4 py-2">
                    <Checkbox
                      checked={!!selected[doc.id]}
                      onChange={e => setSelected(s => ({ ...s, [doc.id]: e.target.checked }))}
                    />
                  </td>

                  <td className="px-4 py-2 max-w-[200px] sm:max-w-[300px]">
                    <div className="flex items-center gap-2 min-w-0">
                      <div className="shrink-0 w-4 h-4 flex items-center justify-center">
                        <FileText size={16} className={brandText} />
                      </div>

                      <span className="min-w-0 flex-1">
                        <span className="truncate text-sm text-gray-800 block w-full">
                          {doc.name}
                        </span>
                      </span>
                    </div>
                  </td>

                  <td className="px-4 py-2 text-right text-gray-600">{doc.sizeKB.toFixed(1)} KB</td>
                  <td className="px-4 py-2 text-right text-gray-600">{doc.uploadedAt ?? '-'}</td>

                  <td className="px-4 py-2">
                    <CategorySelect
                      value={doc.category}
                      options={categoryOptions}
                      onCreate={addCategory}
                      onDeleteOption={removeCategory}
                      onChange={v => onCategoryChange?.(doc.id, v || '')}
                      className="min-w-[160px] flex w-full justify-end"
                      placeholder="카테고리"
                    />
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
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className={`py-4 text-sm ${selectedIds.length ? brandText : 'text-gray-400'}`}>
        {selectedIds.length ? (
          <div
            className={`flex items-center gap-2 rounded-md border px-3 py-2 ${brandBorder} ${brandBg}`}
          >
            <span>{selectedIds.length}개 파일이 선택되었습니다.</span>
          </div>
        ) : (
          <span>파일을 선택하면 일괄 작업을 수행할 수 있어요.</span>
        )}
      </div>

      <div className="flex items-center justify-center gap-5 py-3 text-sm">
        <Pagination page={page} totalPages={totalPages} onPageChange={setPage} />
      </div>
    </div>
  );
}
