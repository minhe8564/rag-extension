import { useState } from 'react';
import { FolderOpen, FileText, ChevronDown, ChevronRight, ChevronLeft } from 'lucide-react';
export default function StorageLocation() {
  const dummyFiles = [
    {
      id: 1,
      name: 'hebees_플랫폼_기획서.pdf',
      size: '2.4MB',
      category: '문서',
      storage: 'public',
      currentProgress: '데이터 정제 43%',
      totalProgress: 6,
    },
    {
      id: 2,
      name: 'hebees_AI_모델_실험결과.csv',
      size: '1.1MB',
      category: '데이터',
      storage: 'public',
      currentProgress: '임베딩 생성',
      totalProgress: 33,
    },
    {
      id: 3,
      name: 'hebees_RAG_API_설계서.docx',
      size: '3.8MB',
      category: '문서',
      storage: 'public',
      currentProgress: '임베딩 생성',
      totalProgress: 56,
    },
    {
      id: 4,
      name: 'hebees_챗봇_테스트_로그.json',
      size: '4.2MB',
      category: '로그',
      storage: 'hebees',
      currentProgress: '시작 전',
      totalProgress: 0,
    },
    {
      id: 5,
      name: 'hebees_UI_디자인_리뷰.png',
      size: '950KB',
      category: '이미지',
      storage: 'hebees',
      currentProgress: '완료',
      totalProgress: 100,
    },
    {
      id: 6,
      name: 'hebees_챗봇 리뷰.png',
      size: '440KB',
      category: '로그',
      storage: 'hebees',
      currentProgress: '시작 전',
      totalProgress: 0,
    },
  ];

  const collections = [
    {
      id: 1,
      name: 'public',
      files: dummyFiles.filter((f) => f.storage === 'public'),
    },
    {
      id: 2,
      name: 'hebees',
      files: dummyFiles.filter((f) => f.storage === 'hebees'),
    },
  ];

  const [openCollections, setOpenCollections] = useState<Record<string, boolean>>({
    public: true,
    hebees: true,
  });

  const FILES_PER_PAGE = 5;
  const [currentPage, setCurrentPage] = useState(1);

  const toggleOpen = (name: string) => {
    setOpenCollections((prev) => ({ ...prev, [name]: !prev[name] }));
  };

  return (
    <section className="flex flex-col w-1/2 p-4 border border-gray-200 rounded-xl bg-white">
      <h3 className="text-xl mb-1 font-bold bg-[linear-gradient(90deg,#BE7DB1_10%,#81BAFF_100%)] bg-clip-text text-transparent w-fit">
        저장 위치
      </h3>

      <div className="space-y-4">
        {collections.map((col) => {
          const totalPages = Math.ceil(col.files.length / FILES_PER_PAGE);
          const startIndex = (currentPage - 1) * FILES_PER_PAGE;
          const visibleFiles = col.files.slice(startIndex, startIndex + FILES_PER_PAGE);

          return (
            <div
              key={col.id}
              className="border rounded-lg p-3 hover:bg-[var(--color-hebees-bg)]/40 transition"
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
                  <input type="checkbox" className="accent-[var(--color-hebees)]" />
                  <button
                    onClick={() => toggleOpen(col.name)}
                    className="flex items-center text-sm text-gray-500 hover:text-[var(--color-hebees)] transition"
                  >
                    {openCollections[col.name] ? (
                      <>
                        <ChevronDown size={15} className="" />
                        접기
                      </>
                    ) : (
                      <>
                        <ChevronRight size={15} className="" />
                        보기
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* 파일 목록 */}
              {openCollections[col.name] && (
                <>
                  <ul className="pl-4 text-sm text-gray-700 space-y-1 mt-2">
                    {visibleFiles.map((file) => (
                      <li
                        key={file.id}
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
                    ))}
                  </ul>

                  {/* 페이지네이션 */}
                  {totalPages >= 1 && (
                    <div className="flex justify-center gap-2 items-center">
                      <button
                        onClick={() => setCurrentPage((p) => Math.max(p - 1, 1))}
                        disabled={currentPage === 1}
                        className="flex items-center gap-1 px-2 py-1 text-gray-600 text-xs hover:text-[var(--color-hebees)] disabled:opacity-40 disabled:hover:text-gray-600"
                      >
                        <ChevronLeft size={10} />
                        <span>이전</span>
                      </button>

                      <span className="text-xs font-medium">
                        {currentPage} / {totalPages}
                      </span>

                      <button
                        onClick={() => setCurrentPage((p) => Math.min(p + 1, totalPages))}
                        disabled={currentPage === totalPages}
                        className="flex items-center gap-1 px-2 py-1 text-gray-600 text-xs hover:text-[var(--color-hebees)] disabled:opacity-30 disabled:hover:text-gray-600"
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
