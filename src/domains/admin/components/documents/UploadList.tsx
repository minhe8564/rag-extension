import { Trash2, FileText, ChevronLeft, ChevronRight } from 'lucide-react';
import { useState } from 'react';
import type { UploadedDocumentsProps } from '@/domains/admin/types/documents.types';

export default function UploadedDocuments({
  files,
  onFilesChange,
  onSelectFiles,
  selectedFiles,
}: UploadedDocumentsProps) {
  // 벡터화 목록으로 보낼 파일 배열

  // 페이지네이션
  const FILES_PER_PAGE = 8;
  const [currentPage, setCurrentPage] = useState(1);
  const totalPages = Math.ceil(files.length / FILES_PER_PAGE);
  const startIndex = (currentPage - 1) * FILES_PER_PAGE;
  const visibleFiles = files.slice(startIndex, startIndex + FILES_PER_PAGE);

  // 전체 선택 여부 계산
  const allSelected = selectedFiles.length === files.length && files.length > 0;

  // 전체 선택 / 해제
  const handleToggleAll = () => {
    if (allSelected) {
      onSelectFiles([]); // 모두 해제
    } else {
      onSelectFiles(files); // 모두 선택
    }
  };

  // 개별 파일 선택 / 해제
  // const handleToggleFile = (file: FileType) => {
  //   const isSelected = selectedFiles.some((f) => f.name === file.name);
  //   if (isSelected) {
  //     onSelectFiles(selectedFiles.filter((f) => f.name !== file.name));
  //   } else {
  //     onSelectFiles([...selectedFiles, file]);
  //   }
  // };

  // 파일 삭제
  const handleDelete = () => {
    const selectedNames = new Set(selectedFiles.map((f) => f.name));
    const remaining = files.filter((f) => !selectedNames.has(f.name));
    onFilesChange?.(remaining);
    onSelectFiles([]); // 삭제 후 선택 초기화
  };

  // 페이지 이동
  const goToPage = (page: number) => {
    setCurrentPage(page);
  };

  return (
    <section className="flex flex-col w-1/2 p-4 border border-gray-200 rounded-xl">
      <h3
        className="text-xl font-bold bg-[linear-gradient(90deg,#BE7DB1_10%,#81BAFF_100%)] 
             bg-clip-text text-transparent w-fit"
      >
        업로드 된 문서
      </h3>

      <div className="flex items-center justify-end gap-3 mb-3 text-sm text-gray-600">
        <label className="flex items-center gap-1 cursor-pointer">
          <p>모두 선택</p>
          <input
            type="checkbox"
            checked={allSelected}
            onChange={handleToggleAll}
            className="
            accent-[var(--color-hebees)]
            border-2 border-[var(--color-hebees)]
            rounded-sm cursor-pointer scale-125 ml-1
          "
          />
        </label>
        <label className="flex items-center gap-1 cursor-pointer">
          <p>삭제</p>
          <button
            onClick={handleDelete}
            disabled={selectedFiles.length === 0}
            className="text-[var(--color-hebees)] transition"
          >
            <Trash2 className="w-5 h-5" />
          </button>
        </label>
      </div>

      {/* 파일 목록 */}
      {visibleFiles.length > 0 ? (
        <ul className="pl-4 text-sm text-gray-700 space-y-1 mt-2 min-h-[300px]">
          {visibleFiles.map((file) => (
            <li
              key={file.name}
              // onClick={() => handleToggleFile(file)}
              className="flex items-center justify-between pt-2 border-b border-gray-100 pb-1 last:border-none cursor-pointer hover:bg-[var(--color-hebees-bg)]/50 hover:ring-1 hover:ring-[var(--color-hebees)]"
            >
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 bg-[var(--color-hebees)] rounded-md flex items-center justify-center">
                  <FileText size={17} className="text-[var(--color-white)]" />
                </div>
                <span className="truncate max-w-[220px] text-center text-xs font-regular">
                  {file.name}
                </span>
              </div>
              <input
                type="checkbox"
                checked={selectedFiles.some((f) => f.name === file.name)}
                onClick={(e) => e.stopPropagation()}
                // onChange={() => handleToggleFile(file)}
                className="accent-[var(--color-hebees)] border-2 border-[var(--color-hebees)] rounded-sm cursor-pointer scale-110"
              />
            </li>
          ))}
        </ul>
      ) : (
        <div className="flex flex-col items-center justify-center flex-1 text-gray-400 text-sm py-10">
          업로드된 문서가 없습니다.
        </div>
      )}

      {/* 페이지네이션 */}
      {totalPages > 1 && (
        <div className="flex justify-center gap-2 items-center mt-3">
          <button
            onClick={() => goToPage(Math.max(currentPage - 1, 1))}
            disabled={currentPage === 1}
            className="flex items-center gap-1 px-2 py-1 text-gray-600 text-xs hover:text-[var(--color-hebees)] disabled:opacity-40"
          >
            <ChevronLeft size={10} />
            <span>이전</span>
          </button>

          <span className="text-xs font-medium">
            {currentPage} / {totalPages}
          </span>

          <button
            onClick={() => goToPage(Math.min(currentPage + 1, totalPages))}
            disabled={currentPage === totalPages}
            className="flex items-center gap-1 px-2 py-1 text-gray-600 text-xs hover:text-[var(--color-hebees)] disabled:opacity-40"
          >
            <span>다음</span>
            <ChevronRight size={10} />
          </button>
        </div>
      )}
    </section>
  );
}
