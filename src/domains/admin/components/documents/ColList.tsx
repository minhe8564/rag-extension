import { useState, useEffect } from 'react';
import { useQuery, useQueries, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  FolderOpen,
  FileText,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  ChevronRight as ChevronRightIcon,
  Trash2,
  Download,
} from 'lucide-react';
import { getCollections, getDocInCollections } from '@/domains/admin/api/documents.api';
import type { collectionType, documentDatatype } from '@/domains/admin/types/documents.types';
import { deleteFile, downloadFile } from '@/shared/api/file.api';
import { toast } from 'react-toastify';

export default function ColList() {
  const [open, setOpen] = useState<Record<string, boolean>>({});
  const [page, setPage] = useState<Record<string, number>>({});
  const [selectedCollections, setSelectedCollections] = useState<Set<string>>(new Set());
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set());
  const [hoveredCollection, setHoveredCollection] = useState<string | null>(null);

  const FILES_PER_PAGE = 5;

  // 컬렉션 목록 조회
  const { data: collectionsResult } = useQuery({
    queryKey: ['collections'],
    queryFn: () => getCollections(),
  });

  const collections = collectionsResult?.data ?? [];
  //  각 컬렉션의 문서 쿼리 (React Query로 병렬 관리)
  const docsQueries = useQueries({
    queries: collections.map((col) => ({
      queryKey: ['docs', col.collectionNo],
      queryFn: () => getDocInCollections(col.collectionNo),
      select: (res: { data: documentDatatype[] }) => res.data,
      enabled: !!open[col.collectionNo], // 열린 컬렉션만 API 요청
    })),
  });

  // 보기 버튼 클릭
  const handleViewClick = (collectionNo: string) => {
    setOpen((prev) => ({
      ...prev,
      [collectionNo]: !prev[collectionNo],
    }));
  };

  // 컬렉션 선택 토글
  const toggleSelectCollection = (colNo: string) => {
    setSelectedCollections((prev) => {
      const next = new Set(prev);
      const willSelect = !next.has(colNo);
      if (willSelect) next.add(colNo);
      else next.delete(colNo);
      return next;
    });
  };

  // 파일 선택
  const toggleSelectFile = (colNo: string, fileNo: string) => {
    const key = `${colNo}::${fileNo}`;
    setSelectedFiles((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const queryClient = useQueryClient();

  // 문서 삭제
  const handleDeleteDoc = async (fileNo: string, colNo: string) => {
    try {
      const data = await deleteFile(fileNo);
      const isSuccess = data.deleted;
      console.log('삭제 성공 여부:', isSuccess);

      // 서버에서 실제로 삭제 성공했는지 확인
      if (!isSuccess) {
        toast.error('서버에서 문서를 삭제하지 못했습니다 ❌');
        return;
      }

      // React Query 캐시 업데이트
      const key = ['docs', colNo];
      const old = queryClient.getQueryData<documentDatatype[]>(key);

      if (Array.isArray(old)) {
        queryClient.setQueryData(
          key,
          old.filter((doc) => doc.fileNo !== fileNo)
        );
      }

      // 항상 최신화 (서버 데이터 동기화)
      queryClient.invalidateQueries({ queryKey: key });

      toast.success('삭제 완료 ✅');
    } catch (error) {
      toast.error('삭제 실패 ❌');
      console.error('파일 삭제 오류:', error);
    }
  };

  // 문서 다운로드
  const handleDownloadDoc = async (fileNo: string, fileName: string) => {
    console.log(fileNo, '@@', fileName);

    try {
      const result = await downloadFile(fileNo, {
        inline: false,
      });
      const url = result.data.url;
      console.log(fileNo, fileName);

      const link = document.createElement('a');
      link.href = url;
      link.download = fileName;
      link.click();
    } catch (error) {
      toast.error('문서 다운로드 중 오류가 발생했습니다.');
      console.log(error);
    }
  };

  return (
    <section className="flex flex-col w-full rounded-xl border-gray-200 bg-white box-border space-y-3 flex-shrink-0 overflow-hidden [scrollbar-gutter:stable]">
      {/* 선택 삭제 버튼 */}
      <div className="flex justify-end p-2">
        <button
          disabled={selectedFiles.size === 0}
          className="flex items-center gap-1 px-3 py-1.5 text-white text-xs font-semibold rounded-md bg-[linear-gradient(90deg,#BE7DB1_10%,#81BAFF_100%)] disabled:opacity-40 hover:opacity-90 transition"
        >
          <Trash2 size={14} />
          선택 삭제
        </button>
      </div>

      {/* 컬렉션 목록 */}
      {collections.map((col, index) => {
        const colNo = col.collectionNo;
        const docsQuery = docsQueries[index];
        const docs = docsQuery?.data || [];
        const isDocsLoading = docsQuery?.isLoading;

        const currentPage = page[colNo] || 1;
        const start = (currentPage - 1) * FILES_PER_PAGE;
        const totalFiles = docs.length;
        const visibleFiles = docs.slice(start, start + FILES_PER_PAGE);
        const totalPages = Math.ceil(totalFiles / FILES_PER_PAGE);

        return (
          <div
            key={colNo}
            onMouseLeave={() => setHoveredCollection((prev) => (prev === colNo ? null : prev))}
            className={`border rounded-lg p-3 transition cursor-pointer ${
              selectedCollections.has(colNo)
                ? 'bg-[var(--color-hebees-bg)]/40 ring-1 ring-[var(--color-hebees)]'
                : hoveredCollection === colNo
                  ? ''
                  : 'hover:bg-[var(--color-hebees-bg)]/50 hover:ring-1 hover:ring-[var(--color-hebees)]'
            }`}
          >
            {/* 헤더 */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 font-medium text-gray-800">
                <div className="w-8 h-8 bg-[var(--color-hebees)] rounded-md flex items-center justify-center">
                  <FolderOpen className="text-[var(--color-white)] w-5 h-5" />
                </div>
                {col.name}
              </div>
              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  className="accent-[var(--color-hebees)] cursor-pointer"
                  checked={selectedCollections.has(colNo)}
                  onClick={(e) => e.stopPropagation()}
                  onChange={() => toggleSelectCollection(colNo)}
                />
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleViewClick(colNo);
                  }}
                  className="flex items-center text-sm text-gray-500 hover:text-[var(--color-hebees)] transition"
                >
                  {open[colNo] ? (
                    <>
                      <ChevronDown size={15} /> 접기
                    </>
                  ) : (
                    <>
                      <ChevronRightIcon size={15} /> 보기
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* 파일 목록 */}
            {open[colNo] && (
              <>
                {isDocsLoading ? (
                  <p className="pl-5 text-xs text-gray-400 py-2">문서를 불러오는 중...</p>
                ) : totalFiles === 0 ? (
                  <p className="pl-5 text-xs text-gray-400 py-2">등록된 문서가 없습니다.</p>
                ) : (
                  <ul className="pl-4 text-xs text-gray-700 space-y-2 mt-2">
                    {visibleFiles.map((file) => (
                      <li
                        key={file.fileNo}
                        onClick={(e) => {
                          e.stopPropagation();
                          toggleSelectFile(colNo, file.fileNo);
                        }}
                        className="flex items-center justify-between border-b border-gray-100 pb-2 last:border-none cursor-pointer hover:bg-[var(--color-hebees-bg)]/60"
                      >
                        {/* 파일 정보 */}
                        <div className="flex flex-col sm:flex-row sm:items-center sm:gap-3 text-[13px] w-full">
                          <div className="flex items-center gap-2 w-[260px]">
                            <div className="w-6 h-6 bg-[var(--color-hebees)] rounded-md flex items-center justify-center">
                              <FileText size={14} className="text-[var(--color-white)]" />
                            </div>
                            <span className="truncate max-w-[200px] font-medium">{file.name}</span>
                          </div>

                          {/* 파일 세부 정보 */}
                          <div className="flex flex-wrap sm:flex-nowrap items-center gap-x-4 gap-y-1 text-gray-500">
                            <span className="whitespace-nowrap">{file.size} KB</span>
                            <span className="whitespace-nowrap">
                              {collections.find((c) => c.collectionNo === file.collectionNo)
                                ?.name || '알 수 없음'}
                            </span>
                            <span className="whitespace-nowrap">
                              {new Date(file.createdAt).toLocaleString()}
                            </span>
                          </div>
                        </div>

                        {/* 선택 및 삭제 */}
                        <div className="flex items-center gap-2 ml-4">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDownloadDoc(file.fileNo, file.name);
                            }}
                            className="text-[var(--color-hebees)] hover:opacity-80 transition"
                          >
                            <Download size={16} />
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDeleteDoc(file.fileNo, colNo);
                            }}
                            className="text-[var(--color-hebees)] hover:opacity-80 transition"
                          >
                            <Trash2 size={16} />
                          </button>
                          <input
                            type="checkbox"
                            className="accent-[var(--color-hebees)] cursor-pointer"
                            checked={selectedFiles.has(`${colNo}::${file.fileNo}`)}
                            onClick={(e) => e.stopPropagation()}
                            onChange={() => toggleSelectFile(colNo, file.fileNo)}
                          />
                        </div>
                      </li>
                    ))}
                  </ul>
                )}

                {/* 페이지네이션 */}
                {totalPages > 1 && (
                  <div className="flex justify-center gap-2 items-center mt-2">
                    <button
                      onClick={() =>
                        setPage((prev) => ({
                          ...prev,
                          [colNo]: Math.max((prev[colNo] || 1) - 1, 1),
                        }))
                      }
                      disabled={currentPage === 1}
                      className="flex items-center gap-1 px-2 py-1 text-gray-600 text-xs hover:text-[var(--color-hebees)] disabled:opacity-40"
                    >
                      <ChevronLeft size={15} />
                      <span>이전</span>
                    </button>
                    <span className="text-xs font-medium">
                      {currentPage} / {totalPages}
                    </span>
                    <button
                      onClick={() =>
                        setPage((prev) => ({
                          ...prev,
                          [colNo]: Math.min((prev[colNo] || 1) + 1, totalPages),
                        }))
                      }
                      disabled={currentPage === totalPages}
                      className="flex items-center gap-1 px-2 py-1 text-gray-600 text-xs hover:text-[var(--color-hebees)] disabled:opacity-30"
                    >
                      <span>다음</span>
                      <ChevronRight size={15} />
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        );
      })}
    </section>
  );
}
