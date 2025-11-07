import { FileText, ChevronLeft, ChevronRight, X } from 'lucide-react';
import { useState, useEffect } from 'react';
import VecProcess from './VecProcess';
import type { RawMyDoc } from '@/shared/types/file.types';
import { useCategoryStore } from '@/shared/store/categoryMap';
// import {uploadFiles} from '@/shared/api/file.api';
// import UploadedFileList from '@/shared/components/file/UploadedFileList';

export default function SelectVectorization({
  finalSelectedFiles,
  onRemove,
}: {
  finalSelectedFiles: RawMyDoc[];
  onRemove?: (file: RawMyDoc) => void;
}) {
  const [localFiles, setLocalFiles] = useState<RawMyDoc[]>(finalSelectedFiles);
  const [selectedFile, setSelectedFile] = useState<RawMyDoc | null>(null);

  const itemsPerPage = 5;
  const [currentPage, setCurrentPage] = useState(1);

  const startIndex = (currentPage - 1) * itemsPerPage;
  const currentFiles = localFiles.slice(startIndex, startIndex + itemsPerPage);
  const totalPages = Math.ceil(localFiles.length / itemsPerPage);

  const categoryMap = useCategoryStore((s) => s.categoryMap);
  const handleRemove = (fileToRemove: RawMyDoc) => {
    onRemove?.(fileToRemove);
    setLocalFiles((prev) =>
      prev.filter(
        (file) =>
          !(file.name === fileToRemove.name && file.collectionNo === fileToRemove.collectionNo)
      )
    );

    if (
      selectedFile &&
      selectedFile.name === fileToRemove.name &&
      selectedFile.collectionNo === fileToRemove.collectionNo
    ) {
      setSelectedFile(null);
    }
  };

  // const handleUpload = async () => {
  //   const groupByCategory = UploadedFileList
  // }
  // 상위에서 finalSelectedFiles 변경 시 반영
  useEffect(() => {
    setLocalFiles(finalSelectedFiles);
  }, [finalSelectedFiles]);

  return (
    <section className="flex flex-col w-full mt-3 p-4 mb-10 border rounded-xl bg-white">
      <h3
        className="text-xl font-bold bg-[linear-gradient(90deg,#BE7DB1_10%,#81BAFF_100%)] 
             bg-clip-text text-transparent w-fit"
      >
        선택 목록
      </h3>

      {/* 테이블 헤더 */}
      <div className="grid grid-cols-8 mt-2 text-sm font-semibold text-gray-800 border-b pb-2">
        <span className="col-span-3 text-center">파일명</span>
        <span className="text-center">크기</span>
        <span className="text-center">카테고리</span>
        <span className="text-center">저장위치</span>
        <span className="text-center">현재 진행률</span>
        <span className="text-center">전체 진행률</span>
      </div>

      {/* 파일 목록 */}
      <div className="flex flex-col min-h-[200px]">
        {currentFiles.length === 0 ? (
          <div className="flex justify-center items-center h-[180px] text-gray-400 text-sm">
            선택된 파일이 없습니다.
          </div>
        ) : (
          currentFiles.map((file) => {
            const categoryName =
              (file.categoryNo && categoryMap[file.categoryNo]) || file.categoryNo || '기타';

            return (
              <div
                key={`${file.name}::${file.collectionNo}`}
                onClick={() => setSelectedFile(file)}
                className={`grid grid-cols-8 items-center text-sm p-2 border-b last:border-none hover:bg-gray-100 cursor-pointer ${
                  selectedFile &&
                  selectedFile.name === file.name &&
                  selectedFile.collectionNo === file.collectionNo
                    ? 'bg-gray-200 ring-1 ring-[var(--color-hebees)]'
                    : ''
                }`}
              >
                {/* 파일명 */}
                <div className="col-span-3 flex items-center gap-2 text-xs pl-2">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleRemove(file);
                    }}
                  >
                    <X size={17} className="text-[var(--color-hebees)]" />
                  </button>
                  <div className="w-7 h-7 bg-[var(--color-hebees)] rounded-md flex items-center justify-center">
                    <FileText size={17} className="text-[var(--color-white)]" />
                  </div>
                  {file.name}
                </div>

                {/* 크기 */}
                <span className="text-center text-xs font-regular">
                  {(file.size / 1024).toFixed(1)} KB
                </span>

                {/* 카테고리 */}
                <span className="text-center text-xs font-regular">{categoryName}</span>

                {/* 저장 위치 */}
                <span className="text-center text-xs font-regular">{file.collectionNo || '-'}</span>

                {/* 진행률 (VecProcess 붙으면 실제 표시됨) */}
                <span className="text-center text-xs font-regular">-</span>
                <span className="text-center text-xs font-regular">-</span>
              </div>
            );
          })
        )}
      </div>

      {/* 페이지네이션 */}
      {localFiles.length > 0 && (
        <div className="flex justify-center gap-2 items-center mt-4">
          <button
            onClick={() => setCurrentPage((p) => Math.max(p - 1, 1))}
            disabled={currentPage === 1}
            className="flex items-center gap-1 px-2 py-1 text-gray-600 text-xs hover:text-[var(--color-hebees)] disabled:opacity-40"
          >
            <ChevronLeft size={10} />
            <span>이전</span>
          </button>

          <span className="text-xs font-medium">
            {currentPage} / {totalPages || 1}
          </span>

          <button
            onClick={() => setCurrentPage((p) => Math.min(p + 1, totalPages))}
            disabled={currentPage === totalPages}
            className="flex items-center gap-1 px-2 py-1 text-gray-600 text-xs hover:text-[var(--color-hebees)] disabled:opacity-40"
          >
            <span>다음</span>
            <ChevronRight size={10} />
          </button>
        </div>
      )}

      {/* 벡터화 실행 버튼 */}
      <div className="flex justify-center">
        <button
          onClick={() => console.log('벡터화 실행')}
          className="
            mt-6 mb-4 px-10 py-2
            text-white font-semibold
            rounded-md
            bg-[linear-gradient(90deg,#BE7DB1_10%,#81BAFF_100%)]
            hover:opacity-90
            transition
            shadow-md
          "
        >
          벡터화 실행
        </button>
      </div>

      {/* VecProcess 표시 */}
      {selectedFile && (
        <VecProcess
          selectedFiles={localFiles}
          initialFileName={selectedFile.name}
          initialCollection={selectedFile.collectionNo || ''}
        />
      )}
    </section>
  );
}
