import { Trash2, FileText, ChevronLeft, ChevronRight } from 'lucide-react';
import { useEffect, useState } from 'react';
// import type { FileType } from '@/domains/admin/types';

interface UploadedDocumentsProps {
  files: File[];
  onFilesChange?: (updatedFiles: File[]) => void; // 부모에 반영하고 싶을 때 사용
  onSelectFiles: (selectedFiles: File[]) => void; // 컬렉션 선택으로 넘길 파일을 부모로 전달
}

export default function UploadedDocuments({
  files,
  onFilesChange,
  onSelectFiles,
}: UploadedDocumentsProps) {
  const [checkedFiles, setCheckedFiles] = useState<string[]>([]);
  const allSelected = checkedFiles.length === files.length && files.length > 0;
  const [currentPage, setCurrentPage] = useState(1);

  // 벡터화 목록으로 보낼 파일 배열
  const [selectedFilesForVector, setSelectedFilesForVector] = useState<File[]>([]);

  // 페이지네이션
  const FILES_PER_PAGE = 8;
  const totalPages = Math.ceil(files.length / FILES_PER_PAGE);
  const startIndex = (currentPage - 1) * FILES_PER_PAGE;
  const visibleFiles = files.slice(startIndex, startIndex + FILES_PER_PAGE);

  // 페이지 이동
  const goToPage = (page: number) => {
    setCurrentPage(page);
  };

  // 개별 파일 선택 토글
  const toggleFile = (fileName: string) => {
    setCheckedFiles((prev) =>
      prev.includes(fileName) ? prev.filter((name) => name !== fileName) : [...prev, fileName]
    );
  };

  // 선택 목록으로 보낼 파일(개별) 업데이트
  const handleCheckFile = (file: File) => {
    setSelectedFilesForVector((prev) => {
      // 이미 선택된 경우 → 해제
      if (prev.includes(file)) {
        return prev.filter((f) => f !== file);
      }
      // 새로 선택된 경우 → 추가
      return [...prev, file];
    });
  };

  // 모두 선택 / 해제
  const toggleAll = () => {
    if (allSelected) {
      setCheckedFiles([]);
      setSelectedFilesForVector([]);
    } else {
      setCheckedFiles(files.map((f) => f.name));
      setSelectedFilesForVector(files);
    }
  };

  // 선택된 파일 삭제
  const handleDelete = () => {
    const remaining = files.filter((f) => !checkedFiles.includes(f.name));
    setCheckedFiles([]);
    onFilesChange?.(remaining);
  };

  // 선택된 파일이 변경될 때마다 부모 컴포넌트로 전달
  useEffect(() => {
    onSelectFiles(selectedFilesForVector);
  }, [selectedFilesForVector]);

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
            onChange={toggleAll}
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
            disabled={checkedFiles.length === 0}
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
              className="flex items-center justify-between border-b border-gray-100 pb-1 last:border-none"
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
                checked={checkedFiles.includes(file.name)}
                onChange={() => {
                  toggleFile(file.name);
                  handleCheckFile(file);
                }}
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
