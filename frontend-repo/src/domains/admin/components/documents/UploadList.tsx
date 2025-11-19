import { Trash2, FileText, ChevronLeft, ChevronRight } from 'lucide-react';
import { useState } from 'react';
import type { RawMyDoc } from '@/shared/types/file.types';
import { useCategoryStore } from '@/shared/store/useCategoryMap';

type UploadListProps = {
  files: RawMyDoc[];
  onFilesChange?: (nextFiles: RawMyDoc[]) => void;
  onSelectFiles: (selected: RawMyDoc[]) => void;
  selectedFiles: RawMyDoc[];
};

export default function UploadList({
  files,
  onFilesChange,
  onSelectFiles,
  selectedFiles,
}: UploadListProps) {
  const FILES_PER_PAGE = 5;
  const [currentPage, setCurrentPage] = useState(1);
  const totalPages = Math.ceil(files.length / FILES_PER_PAGE);
  const startIndex = (currentPage - 1) * FILES_PER_PAGE;
  const visibleFiles = files.slice(startIndex, startIndex + FILES_PER_PAGE);
  const categoryMap = useCategoryStore((s) => s.categoryMap);
  const allSelected = selectedFiles.length === files.length && files.length > 0;

  const handleToggleAll = () => {
    if (allSelected) onSelectFiles([]);
    else onSelectFiles(files);
  };

  const handleToggleFile = (file: RawMyDoc) => {
    const isSelected = selectedFiles.some((f) => f.fileNo === file.fileNo);
    if (isSelected) onSelectFiles(selectedFiles.filter((f) => f.fileNo !== file.fileNo));
    else onSelectFiles([...selectedFiles, file]);
  };

  const handleDelete = () => {
    const selectedIds = new Set(selectedFiles.map((f) => f.fileNo));
    const remaining = files.filter((f) => !selectedIds.has(f.fileNo));
    onFilesChange?.(remaining);
    onSelectFiles([]);
  };

  const formatFileSize = (size: number) => {
    if (size >= 1024 * 1024) return `${(size / 1024 / 1024).toFixed(1)} MB`;
    return `${(size / 1024).toFixed(1)} KB`;
  };

  const goToPage = (page: number) => setCurrentPage(page);

  // 카테고리 매핑
  return (
    <section className="flex flex-col w-full p-5 min-h-[475px] border border-gray-200 rounded-xl bg-white shadow-sm">
      {/* 헤더 */}
      <h3 className="text-xl font-extrabold bg-[linear-gradient(90deg,#BE7DB1_10%,#81BAFF_100%)] bg-clip-text text-transparent w-fit mb-3">
        업로드 할 문서
      </h3>

      {/* 상단 컨트롤 */}
      <div className="flex items-center justify-end gap-4 mb-3 text-sm text-gray-600">
        <label className="flex items-center gap-1 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={allSelected}
            onChange={handleToggleAll}
            className="accent-[var(--color-hebees)] border-2 border-[var(--color-hebees)] rounded-sm cursor-pointer scale-110"
          />
          <span>모두 선택</span>
        </label>

        <button
          onClick={handleDelete}
          disabled={selectedFiles.length === 0}
          className="flex items-center gap-1 text-[var(--color-hebees)] disabled:opacity-40 transition"
        >
          <Trash2 className="w-4 h-4" />
          <span>삭제</span>
        </button>
      </div>

      {/* 파일 리스트 */}
      <div className="border-t border-gray-100 pt-2 min-h-[260px]">
        {visibleFiles.length > 0 ? (
          <ul className="space-y-1">
            {visibleFiles.map((file) => {
              const isChecked = selectedFiles.some((f) => f.fileNo === file.fileNo);

              const categoryName =
                (file.categoryNo && categoryMap[file.categoryNo]) || file.categoryNo || '기타';
              return (
                <li
                  key={file.fileNo}
                  onClick={() => handleToggleFile(file)}
                  className={`flex items-center justify-between px-3 py-2 rounded-md transition cursor-pointer ${
                    isChecked
                      ? 'bg-[var(--color-hebees-bg)]/70 ring-1 ring-[var(--color-hebees)]'
                      : 'hover:bg-[var(--color-hebees-bg)]/40 hover:ring-1 hover:ring-[var(--color-hebees)]'
                  }`}
                >
                  {/* 왼쪽: 아이콘 + 파일명 */}
                  <div className="flex items-center gap-3 flex-1">
                    <div className="w-8 h-8 bg-[var(--color-hebees)] rounded-md flex items-center justify-center shrink-0">
                      <FileText size={20} className="text-white" />
                    </div>

                    <div className="flex items-center justify-between w-full">
                      <span className="truncate text-sm font-medium text-gray-800 max-w-[220px]">
                        {file.name}
                      </span>

                      {/* 오른쪽: 카테고리 + 파일 크기 */}
                      <div className="flex items-center gap-4 text-xs text-gray-500 whitespace-nowrap">
                        <span className="flex items-center gap-1">
                          <span>{categoryName}</span>
                        </span>
                        <span className="flex items-center gap-1">
                          <span>{formatFileSize(file.size)}</span>
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* 체크박스 */}
                  <input
                    type="checkbox"
                    checked={isChecked}
                    onClick={(e) => e.stopPropagation()}
                    onChange={() => handleToggleFile(file)}
                    className="ml-3 accent-[var(--color-hebees)] border-2 border-[var(--color-hebees)] rounded-sm cursor-pointer scale-110 shrink-0"
                  />
                </li>
              );
            })}
          </ul>
        ) : (
          <div className="flex flex-col items-center justify-center text-gray-400 text-sm py-14">
            업로드된 문서가 없습니다.
          </div>
        )}
      </div>

      {/* 페이지네이션 */}
      {totalPages > 1 && (
        <div className="flex justify-center gap-2 items-center mt-4">
          <button
            onClick={() => goToPage(Math.max(currentPage - 1, 1))}
            disabled={currentPage === 1}
            className="flex items-center gap-1 px-2 py-1 text-xs text-gray-600 hover:text-[var(--color-hebees)] disabled:opacity-40"
          >
            <ChevronLeft size={10} />
            <span>이전</span>
          </button>

          <span className="text-xs font-medium text-gray-700">
            {currentPage} / {totalPages}
          </span>

          <button
            onClick={() => goToPage(Math.min(currentPage + 1, totalPages))}
            disabled={currentPage === totalPages}
            className="flex items-center gap-1 px-2 py-1 text-xs text-gray-600 hover:text-[var(--color-hebees)] disabled:opacity-40"
          >
            <span>다음</span>
            <ChevronRight size={10} />
          </button>
        </div>
      )}
    </section>
  );
}
