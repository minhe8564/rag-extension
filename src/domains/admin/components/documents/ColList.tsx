import { useState } from 'react';
import { FolderOpen, FileText, ChevronLeft, ChevronRight, ChevronDown } from 'lucide-react';
export default function ColList() {
  const dummyCollections = [
    {
      id: 1,
      name: 'public',
      files: [
        { id: 101, name: '헵비스_RAG 실험 데이터셋 요약 보고서.pdf' },
        { id: 102, name: '헵비스_RAG 벡터 변환 테스트 결과.xlsx' },
      ],
    },
    {
      id: 2,
      name: 'private',
      files: [
        { id: 201, name: '내부 검증용 데이터셋 리스트.csv' },
        { id: 202, name: '내부 문서 벡터화 파이프라인 노트.docx' },
      ],
    },
    {
      id: 3,
      name: 'retina',
      files: [
        { id: 301, name: '안경점 고객 피드백 벡터 분석 결과.json' },
        { id: 302, name: '안경 프레임 분류 실험 리포트.pdf' },
      ],
    },
    {
      id: 4,
      name: 'hebees',
      files: [
        { id: 401, name: 'HEBEES 검색 질의 최적화 결과.xlsx' },
        { id: 402, name: 'HEBEES 문서 전처리 가이드라인.txt' },
      ],
    },
    {
      id: 5,
      name: 'logs',
      files: [
        { id: 501, name: 'LLM 호출 로그 기록 2025-10-21.log' },
        { id: 502, name: 'API 요청 응답 분석 메모.md' },
      ],
    },
    {
      id: 6,
      name: 'archive',
      files: [
        { id: 601, name: '이전 RAG 실험 백업 데이터.zip' },
        { id: 602, name: '2025년 상반기 모델 학습 보고서.pdf' },
      ],
    },
  ];

  const [open, setOpen] = useState<Record<string, boolean>>({});
  const [page, setPage] = useState<Record<string, number>>({});
  const FILES_PER_PAGE = 5;

  const toggleOpen = (name: string) => setOpen((prev) => ({ ...prev, [name]: !prev[name] }));

  return (
    <>
      <section className="flex flex-col w-full rounded-xl border-gray-200 bg-white box-border space-y-3 flex-shrink-0 overflow-hidden [scrollbar-gutter:stable]">
        {dummyCollections.map((col) => {
          const currentPage = page[col.name] || 1;
          const totalPages = Math.ceil(col.files.length / FILES_PER_PAGE);
          const start = (currentPage - 1) * FILES_PER_PAGE;
          const visibleFiles = col.files.slice(start, start + FILES_PER_PAGE);

          return (
            <div
              key={col.id}
              className="border rounded-lg p-3 hover:bg-[var(--color-hebees-bg)]/50 transition"
            >
              {/* 컬렉션 헤더 */}
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
                    {open[col.name] ? (
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
              {open[col.name] && (
                <>
                  <ul className="pl-4 text-xs text-gray-700 space-y-2 mt-2">
                    {visibleFiles.map((file) => (
                      <li
                        key={file.id}
                        className="flex items-center justify-between border-b border-gray-100 pb-2 last:border-none"
                      >
                        <div className="flex items-center gap-2">
                          <div className="w-6 h-6 bg-[var(--color-hebees)] rounded-md flex items-center justify-center">
                            <FileText size={14} className="text-[var(--color-white)]" />
                          </div>
                          <span className="truncate max-w-[260px]">{file.name}</span>
                        </div>
                        <input type="checkbox" className="accent-[var(--color-hebees)]" />
                      </li>
                    ))}
                  </ul>

                  {/* 페이지네이션 */}
                  {totalPages >= 1 && (
                    <div className="flex justify-center gap-2 items-center">
                      <button
                        onClick={() =>
                          setPage((prev) => ({
                            ...prev,
                            [col.name]: Math.max((prev[col.name] || 1) - 1, 1),
                          }))
                        }
                        disabled={currentPage === 1}
                        className="flex items-center gap-1 px-2 py-1 text-gray-600 text-xs hover:text-[var(--color-hebees)] disabled:opacity-40 disabled:hover:text-gray-600"
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
                            [col.name]: Math.min((prev[col.name] || 1) + 1, totalPages),
                          }))
                        }
                        disabled={currentPage === totalPages}
                        className="flex items-center gap-1 px-2 py-1 text-gray-600 text-xs hover:text-[var(--color-hebees)] disabled:opacity-30 disabled:hover:text-gray-600"
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
    </>
  );
}
