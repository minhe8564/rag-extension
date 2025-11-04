import { useState } from 'react';
import { FolderOpen, FileText, ChevronLeft, ChevronRight, ChevronDown, Trash2 } from 'lucide-react';
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

  const [collections, setCollections] = useState(dummyCollections);
  const [open, setOpen] = useState<Record<string, boolean>>({});
  const [page, setPage] = useState<Record<string, number>>({});
  const FILES_PER_PAGE = 5;

  const [selectedCollections, setSelectedCollections] = useState<Set<string>>(new Set());
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set());
  const [hoveredCollection, setHoveredCollection] = useState<string | null>(null);

  const toggleOpen = (name: string) => setOpen((prev) => ({ ...prev, [name]: !prev[name] }));

  const handleDeleteFile = (colName: string, fileId: number) => {
    setCollections((prev) =>
      prev.map((c) =>
        c.name === colName ? { ...c, files: c.files.filter((f) => f.id !== fileId) } : c
      )
    );
    const key = `${colName}::${fileId}`;
    setSelectedFiles((prev) => {
      const next = new Set(prev);
      next.delete(key);
      return next;
    });
  };

  const toggleSelectCollection = (colName: string) => {
    setSelectedCollections((prev) => {
      const next = new Set(prev);
      const willSelect = !next.has(colName);
      if (willSelect) next.add(colName);
      else next.delete(colName);
      // 컬렉션 토글에 맞춰 파일들도 함께 토글
      const col = collections.find((c) => c.name === colName);
      if (col) {
        setSelectedFiles((prevFiles) => {
          const nextFiles = new Set(prevFiles);
          for (const f of col.files) {
            const key = `${colName}::${f.id}`;
            if (willSelect) nextFiles.add(key);
            else nextFiles.delete(key);
          }
          return nextFiles;
        });
      }
      return next;
    });
  };

  const toggleSelectFile = (colName: string, fileId: number) => {
    const key = `${colName}::${fileId}`;
    setSelectedFiles((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const handleBulkDelete = () => {
    if (selectedFiles.size === 0) return;
    setCollections((prev) =>
      prev.map((c) => ({
        ...c,
        files: c.files.filter((f) => !selectedFiles.has(`${c.name}::${f.id}`)),
      }))
    );
    setSelectedFiles(new Set());
  };

  return (
    <>
      <section className="flex flex-col w-full rounded-xl border-gray-200 bg-white box-border space-y-3 flex-shrink-0 overflow-hidden [scrollbar-gutter:stable]">
        <div className="flex justify-end p-2">
          <button
            onClick={handleBulkDelete}
            disabled={selectedFiles.size === 0}
            className="flex items-center gap-1 px-3 py-1.5 text-white text-xs font-semibold rounded-md bg-[linear-gradient(90deg,#BE7DB1_10%,#81BAFF_100%)] disabled:opacity-40 hover:opacity-90 transition"
          >
            <Trash2 size={14} />
            선택 삭제
          </button>
        </div>
        {collections.map((col) => {
          const currentPage = page[col.name] || 1;
          const totalPages = Math.ceil(col.files.length / FILES_PER_PAGE);
          const start = (currentPage - 1) * FILES_PER_PAGE;
          const visibleFiles = col.files.slice(start, start + FILES_PER_PAGE);

          return (
            <div
              key={col.id}
              onClick={() => toggleSelectCollection(col.name)}
              onMouseLeave={() => setHoveredCollection((prev) => (prev === col.name ? null : prev))}
              className={
                `border rounded-lg p-3 transition cursor-pointer ` +
                (selectedCollections.has(col.name)
                  ? 'bg-[var(--color-hebees-bg)]/40 ring-1 ring-[var(--color-hebees)]'
                  : hoveredCollection === col.name
                    ? ''
                    : 'hover:bg-[var(--color-hebees-bg)]/50 hover:ring-1 hover:ring-[var(--color-hebees)]')
              }
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
                  <input
                    type="checkbox"
                    className="accent-[var(--color-hebees)] cursor-pointer"
                    checked={selectedCollections.has(col.name)}
                    onClick={(e) => e.stopPropagation()}
                    onChange={() => toggleSelectCollection(col.name)}
                  />
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleOpen(col.name);
                    }}
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
                        onClick={(e) => {
                          e.stopPropagation();
                          toggleSelectFile(col.name, file.id);
                        }}
                        onMouseEnter={() => setHoveredCollection(col.name)}
                        onMouseLeave={() =>
                          setHoveredCollection((prev) => (prev === col.name ? null : prev))
                        }
                        className={`flex items-center justify-between border-b border-gray-100 pb-2 last:border-none cursor-pointer hover:bg-[var(--color-hebees-bg)]/60`}
                      >
                        <div className="flex items-center gap-2">
                          <div className="w-6 h-6 bg-[var(--color-hebees)] rounded-md flex items-center justify-center">
                            <FileText size={14} className="text-[var(--color-white)]" />
                          </div>
                          <span className="truncate max-w-[260px]">{file.name}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <input
                            type="checkbox"
                            className="accent-[var(--color-hebees)] cursor-pointer"
                            checked={selectedFiles.has(`${col.name}::${file.id}`)}
                            onClick={(e) => e.stopPropagation()}
                            onChange={() => toggleSelectFile(col.name, file.id)}
                          />
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDeleteFile(col.name, file.id);
                            }}
                            className="text-[var(--color-hebees)] hover:opacity-80 transition"
                          >
                            <Trash2 size={16} />
                          </button>
                        </div>
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
