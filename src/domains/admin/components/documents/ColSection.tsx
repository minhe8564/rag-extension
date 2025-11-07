import { FolderOpen, FileText, ChevronDown, ChevronRight, ChevronLeft } from 'lucide-react';
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import type { RawMyDoc } from '@/shared/types/file.types';
import type { documentDatatype } from '@/domains/admin/types/documents.types';
import { getDocInCollections } from '@/domains/admin/api/documents.api';

type ColSectionProps = {
  selectedCollection: 'public' | 'hebees' | null;
  onCollectionSelect: (name: 'public' | 'hebees' | null) => void;
  // 실제 업로드된 문서 (UploadTab에서 내려줌)
  uploadedFiles?: RawMyDoc[];
};

export default function ColSection({ selectedCollection, onCollectionSelect }: ColSectionProps) {
  const [openCollection, setOpenCollection] = useState<Record<string, boolean>>({
    public: false,
    hebees: false,
  });

  // 훅
  const publicQuery = useQuery({
    queryKey: ['collectionDocs', 'public'],
    queryFn: () => getDocInCollections('public'),
    enabled: openCollection.public,
    staleTime: 1000 * 60 * 5,
  });

  const hebeesQuery = useQuery({
    queryKey: ['collectionDocs', 'hebees'],
    queryFn: () => getDocInCollections('hebees'),
    enabled: openCollection.hebees,
    staleTime: 1000 * 60 * 5,
  });

  const [page, setPage] = useState<Record<string, number>>({ public: 1, hebees: 1 });
  const FILES_PER_PAGE = 5;
  const collections = [
    { id: 1, name: 'public', query: publicQuery },
    { id: 2, name: 'hebees', query: hebeesQuery },
  ];

  // const useCollectionDocs = (collectionNo: string, enabled: boolean) =>
  //   useQuery({
  //     queryKey: ['collectionDocs', collectionNo],
  //     queryFn: () => getDocInCollections(collectionNo),

  //     enabled, //  open 상태일 때만 API 실행
  //     staleTime: 1000 * 60 * 5, // 5분 캐시
  //   });

  const toggleOpen = (name: string) => {
    setOpenCollection((prev) => ({ ...prev, [name]: !prev[name] }));
  };

  const handleSelectCollection = (name: 'public' | 'hebees') => {
    const newSelection = selectedCollection === name ? null : name;
    onCollectionSelect(newSelection);
  };

  return (
    <section className="flex flex-col w-full h-full p-4 border border-gray-200 rounded-xl bg-white">
      <h3 className="text-xl mb-1 font-bold bg-[linear-gradient(90deg,#BE7DB1_10%,#81BAFF_100%)] bg-clip-text text-transparent w-fit">
        저장 위치
      </h3>

      <div className="space-y-4">
        {collections.map((col) => {
          const { data, refetch } = col.query;
          const docs = data?.data as documentDatatype[] | undefined;
          const totalPages = Math.ceil((docs?.length ?? 0) / FILES_PER_PAGE);
          const currentPage = page[col.name] || 1;
          const startIndex = (currentPage - 1) * FILES_PER_PAGE;
          const visibleFiles = docs?.slice(startIndex, startIndex + FILES_PER_PAGE);

          return (
            <div
              key={col.id}
              className={`border rounded-lg p-3 transition cursor-pointer ${
                selectedCollection === col.name
                  ? 'bg-[var(--color-hebees-bg)]/40 ring-1 ring-[var(--color-hebees)]'
                  : 'hover:bg-[var(--color-hebees-bg)]/40 hover:ring-1 hover:ring-[var(--color-hebees)]'
              }`}
              onClick={() => handleSelectCollection(col.name as 'public' | 'hebees')}
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
                    onChange={() => handleSelectCollection(col.name as 'public' | 'hebees')}
                  />
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleOpen(col.name);
                      if (!openCollection[col.name]) refetch();
                    }}
                    className="flex items-center text-sm text-gray-500 hover:text-[var(--color-hebees)] transition"
                  >
                    {openCollection[col.name] ? (
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
              {openCollection[col.name] && (
                <>
                  <ul className="pl-4 text-sm text-gray-700 space-y-1 mt-2">
                    {visibleFiles?.length === 0 ? (
                      <li className="text-gray-400 text-xs">등록된 문서가 없습니다.</li>
                    ) : (
                      visibleFiles?.map((file) => (
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
                            [col.name]: Math.max((prev[col.name] || 1) - 1, 1),
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
                            [col.name]: Math.min((prev[col.name] || 1) + 1, totalPages),
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
