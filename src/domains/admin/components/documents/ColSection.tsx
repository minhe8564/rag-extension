import { FolderOpen, FileText, ChevronDown, ChevronRight, ChevronLeft } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import type { RawMyDoc } from '@/shared/types/file.types';
import type { documentDatatype } from '@/domains/admin/types/documents.types';
import { getDocInCollections, getCollections } from '@/domains/admin/api/documents.api';

type ColSectionProps = {
  selectedCollection: string | null;
  onCollectionSelect: (name: string | null) => void;
  uploadedFiles?: RawMyDoc[];
};

export default function ColSection({ selectedCollection, onCollectionSelect }: ColSectionProps) {
  const [openCollection, setOpenCollection] = useState<Record<string, boolean>>({});
  const [page, setPage] = useState<Record<string, number>>({});
  const [docsByCollection, setDocsByCollection] = useState<Record<string, documentDatatype[]>>({});
  const FILES_PER_PAGE = 5;

  // 컬렉션 목록 조회 (useQuery는 여기 1개만)
  const { data: collectionsResult } = useQuery({
    queryKey: ['collections', { filter: true }],
    queryFn: () => getCollections({ filter: true }),
    staleTime: 1000 * 60 * 10,
  });

  const collections = collectionsResult?.data ?? [];

  // 컬렉션 클릭 시 문서 가져오기
  const handleToggleOpen = (collectionNo: string) => {
    setOpenCollection((prev) => ({
      ...prev,
      [collectionNo]: !prev[collectionNo],
    }));
    onCollectionSelect(collectionNo);
  };

  const { data: docs, isLoading } = useQuery({
    queryKey: ['docs', selectedCollection],
    queryFn: () => getDocInCollections(selectedCollection!).then((res) => res.data),
    enabled: !!selectedCollection && !!openCollection[selectedCollection], // 열렸을 때만 실행
    staleTime: 1000 * 60 * 10, // 3분 캐싱
  });

  useEffect(() => {
    if (collectionsResult) {
      console.log('📌 Collections Response:', collectionsResult);
    }
  }, [collectionsResult]);

  useEffect(() => {
    if (docs && selectedCollection) {
      setDocsByCollection((prev) => ({
        ...prev,
        [selectedCollection]: docs, // 쿼리 결과 저장
      }));
    }
  }, [docs, selectedCollection]);

  const handleSelectCollection = (collectionName: string) => {
    const newSelection = selectedCollection === collectionName ? null : collectionName;
    onCollectionSelect(newSelection);
  };

  return (
    <section className="flex flex-col min-h-[475px] w-full h-full p-4 border border-gray-200 rounded-xl bg-white">
      <h3 className="text-xl mb-3 font-bold bg-[linear-gradient(90deg,#BE7DB1_10%,#81BAFF_100%)] bg-clip-text text-transparent w-fit">
        저장할 컬렉션 선택
      </h3>

      <div className="space-y-4">
        {collections.map((col) => {
          const rawDocs = docsByCollection[col.collectionNo];
          const safeDocs = Array.isArray(rawDocs) ? rawDocs : [];

          const totalPages = Math.ceil(safeDocs.length / FILES_PER_PAGE);

          const currentPage = page[col.collectionNo] || 1;
          const startIndex = (currentPage - 1) * FILES_PER_PAGE;
          const visibleFiles = safeDocs.slice(startIndex, startIndex + FILES_PER_PAGE);

          return (
            <div
              key={col.collectionNo}
              className={`border rounded-lg p-3 transition cursor-pointer ${
                selectedCollection === col.collectionNo
                  ? 'bg-[var(--color-hebees-bg)]/40 ring-1 ring-[var(--color-hebees)]'
                  : 'hover:bg-[var(--color-hebees-bg)]/40 hover:ring-1 hover:ring-[var(--color-hebees)]'
              }`}
              onClick={() => handleSelectCollection(col.name)}
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
                    checked={selectedCollection === col.name}
                    onClick={(e) => e.stopPropagation()}
                    onChange={() => handleSelectCollection(col.name)}
                  />

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleToggleOpen(col.collectionNo);
                    }}
                    className="flex items-center text-sm text-gray-500 hover:text-[var(--color-hebees)] transition"
                  >
                    {openCollection[col.collectionNo] ? (
                      <>
                        <ChevronDown size={15} />
                        접기
                      </>
                    ) : (
                      <>
                        <ChevronRight size={15} />
                        보기
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* 파일 목록 */}
              {openCollection[col.collectionNo] && (
                <>
                  <ul className="pl-4 text-sm text-gray-700 space-y-1 mt-2">
                    {/* 🔹 로딩 중 표시 */}
                    {isLoading && selectedCollection === col.collectionNo ? (
                      <li className="text-gray-400 text-xs animate-pulse">
                        문서 목록을 불러오는 중...
                      </li>
                    ) : visibleFiles.length === 0 ? (
                      <li className="text-gray-400 text-xs">등록된 문서가 없습니다.</li>
                    ) : (
                      visibleFiles.map((file) => (
                        <li
                          key={file.fileNo}
                          className="flex items-center justify-between border-b border-gray-100 pb-1 last:border-none"
                        >
                          <div className="flex items-center gap-2">
                            <div className="w-5 h-5 bg-[var(--color-hebees)] rounded-md flex items-center justify-center">
                              <FileText size={14} className="text-[var(--color-white)]" />
                            </div>
                            <span className="truncate max-w-[220px] text-center text-xs font-regular">
                              {file.name}
                            </span>
                          </div>
                        </li>
                      ))
                    )}
                  </ul>

                  {/* 페이지네이션 */}
                  {totalPages > 1 && (
                    <div className="flex justify-center gap-2 items-center mt-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setPage((prev) => ({
                            ...prev,
                            [col.collectionNo]: Math.max((prev[col.collectionNo] || 1) - 1, 1),
                          }));
                        }}
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
                        onClick={(e) => {
                          e.stopPropagation();
                          setPage((prev) => ({
                            ...prev,
                            [col.collectionNo]: Math.min(
                              (prev[col.collectionNo] || 1) + 1,
                              totalPages
                            ),
                          }));
                        }}
                        disabled={currentPage === totalPages}
                        className="flex items-center gap-1 px-2 py-1 text-gray-600 text-xs hover:text-[var(--color-hebees)] disabled:opacity-40"
                      >
                        <span>다음</span>
                        <ChevronRight size={10} />
                      </button>
                    </div>
                  )}
                </>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}
