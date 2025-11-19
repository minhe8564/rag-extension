import { FileText, ChevronLeft, ChevronRight, X } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import type { RawMyDoc } from '@/shared/types/file.types';
import { useCategoryStore } from '@/shared/store/useCategoryMap';
import { getCollections } from '@/domains/admin/api/documents.api';
import { uploadFiles } from '@/shared/api/file.api';
import { toast } from 'react-toastify';
// import {uploadFiles} from '@/shared/api/file.api';
// import UploadedFileList from '@/shared/components/file/UploadedFileList';

export default function SelectVectorization({
  finalSelectedFiles,
  onRemove,
  onUploadComplete,
  isVectorizing,
  onStartVectorizing,
}: {
  finalSelectedFiles: RawMyDoc[];
  onRemove?: (file: RawMyDoc) => void;
  onUploadComplete: () => void;
  isVectorizing: boolean;
  onStartVectorizing: () => void;
}) {
  const [localFiles, setLocalFiles] = useState<RawMyDoc[]>(finalSelectedFiles);
  const [selectedFile, setSelectedFile] = useState<RawMyDoc | null>(null);

  const itemsPerPage = 5;
  const [currentPage, setCurrentPage] = useState(1);

  const startIndex = (currentPage - 1) * itemsPerPage;
  const currentFiles = localFiles.slice(startIndex, startIndex + itemsPerPage);
  const totalPages = Math.ceil(localFiles.length / itemsPerPage);

  const [isUploading, setIsUploading] = useState(false);

  useEffect(() => {
    setLocalFiles(finalSelectedFiles);
    console.log('@%%%%', finalSelectedFiles);
  }, [finalSelectedFiles]);

  // 업로드
  async function handleUpload(finalSelectedFiles: RawMyDoc[]) {
    try {
      onStartVectorizing();

      setIsUploading(true);

      // 카테고리로 그룹화
      const groupedByCategoryAndCollection = finalSelectedFiles.reduce<Record<string, RawMyDoc[]>>(
        (acc, file) => {
          const categoryNo = file.categoryNo;
          const bucket = file.collectionNo; // 👈 RawMyDoc에 있어야 함

          const key = `${categoryNo}__${bucket}`;

          if (!acc[key]) acc[key] = [];
          acc[key].push(file);
          return acc;
        },
        {}
      );

      // 그룹별로 업로드 요청
      const uploadPromises = Object.entries(groupedByCategoryAndCollection).map(([, files]) => {
        const categoryNo = files[0].categoryNo;
        const bucket = files[0].collectionNo;

        return uploadFiles({
          categoryNo,
          bucket,
          files: files.map((f) => f.originalFile as File),
        });
      });

      await Promise.all(uploadPromises);
      toast.success('파일 업로드 완료!');
      // 초기화
      setLocalFiles([]);
      setSelectedFile(null);
      setCurrentPage(1);

      onUploadComplete();
    } catch (err) {
      console.error('❌ 업로드 실패', err);
      toast.error('업로드 중 오류가 발생했습니다.');
    } finally {
      setIsUploading(false);
    }
  }

  const { data: collectionsResult } = useQuery({
    queryKey: ['collections', { filter: true }],
    queryFn: () => getCollections({ filter: true }),
    staleTime: 1000 * 60 * 10,
  });
  const collections = collectionsResult?.data ?? [];

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

  return (
    <section className="flex flex-col w-full p-4 border rounded-xl bg-white min-h-[475px]">
      <h3
        className="text-xl font-bold bg-[linear-gradient(90deg,#BE7DB1_10%,#81BAFF_100%)] 
           bg-clip-text text-transparent w-fit mb-3"
      >
        벡터화 대상 파일 목록
      </h3>

      {/* 테이블 + 파일 목록 영역 */}
      <div className="flex flex-col flex-1">
        {/* 테이블 헤더 */}
        <div className="grid grid-cols-8 mt-2 h-[40px] text-sm font-semibold text-gray-800 border-b">
          <span className="col-span-3 text-center">파일명</span>
          <span className="text-center col-span-2">크기</span>
          <span className="text-center col-span-2">카테고리</span>
          <span className="text-center col-span-1">저장위치</span>
        </div>

        {/* 파일 목록 */}
        <div
          className={`flex-1 ${currentFiles.length > 0 ? 'h-[270px] overflow-y-auto' : 'h-[270px] flex items-center justify-center'}`}
        >
          {currentFiles.length === 0 ? (
            <div className="flex flex-col justify-center items-center h-full text-gray-400 text-sm">
              선택된 파일이 없습니다.
            </div>
          ) : (
            currentFiles.map((file) => {
              const categoryName =
                (file.categoryNo && categoryMap[file.categoryNo]) || file.categoryNo || '기타';

              return (
                <div
                  key={`${file.name}::${file.collectionNo}`}
                  onClick={() => {
                    if (!isUploading) return;
                    setSelectedFile(file);
                  }}
                  className={`grid grid-cols-8 items-center text-sm border-b p-2 last:border-none transition
              ${isUploading ? 'hover:bg-[var(--color-hebees-bg)]/40 cursor-pointer' : 'cursor-default'}
              ${
                selectedFile &&
                selectedFile.name === file.name &&
                selectedFile.collectionNo === file.collectionNo
                  ? 'bg-gray-200 ring-1 ring-[var(--color-hebees)]'
                  : ''
              }`}
                >
                  {/* 파일명 */}
                  <div className="col-span-3 flex items-center gap-1 text-xs">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRemove(file);
                      }}
                      className="hover:opacity-80 transition"
                    >
                      <X size={16} className="text-[var(--color-hebees)]" />
                    </button>
                    <div className="w-6 h-6 bg-[var(--color-hebees)] rounded-md flex items-center justify-center">
                      <FileText size={16} className="text-[var(--color-white)]" />
                    </div>
                    <span className="truncate max-w-[150px]">{file.name}</span>
                  </div>

                  {/* 크기 */}
                  <span className="col-span-2 text-center text-xs">
                    {(file.size / 1024).toFixed(1)} KB
                  </span>

                  {/* 카테고리 */}
                  <span className="col-span-2 text-center text-xs">{categoryName}</span>

                  {/* 저장위치 */}
                  <span className="col-span-1 text-center text-xs">
                    {' '}
                    {collections.find((c) => c.name === file.collectionNo)?.name || '-'}
                  </span>
                </div>
              );
            })
          )}
        </div>
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
      <div className="flex justify-center mt-6 mb-4">
        <button
          onClick={() => handleUpload(localFiles)}
          disabled={isUploading || localFiles.length === 0}
          className={`px-10 py-2 text-white cursor-pointer font-semibold rounded-md transition shadow-md ${
            isUploading
              ? 'bg-gray-300 cursor-not-allowed'
              : 'bg-[linear-gradient(90deg,#BE7DB1_10%,#81BAFF_100%)] hover:opacity-90'
          }`}
        >
          {isUploading ? '업로드 중...' : isVectorizing ? '벡터화 진행 중...' : '벡터화 실행'}
        </button>
      </div>
    </section>
  );
}
