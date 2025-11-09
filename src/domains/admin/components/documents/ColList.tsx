import { useState, useEffect } from 'react';
import { FolderOpen, FileText, ChevronLeft, ChevronRight, ChevronDown, Trash2 } from 'lucide-react';
import { getCollections, getDocInCollections } from '@/domains/admin/api/documents.api';
import type { collectionType, documentDatatype } from '@/domains/admin/types/documents.types';
import { deleteDocument } from '@/shared/api/file.api';
import { toast } from 'react-toastify';

export default function ColList() {
  const [collections, setCollections] = useState<collectionType[]>([]);
  const [open, setOpen] = useState<Record<string, boolean>>({});
  const [page, setPage] = useState<Record<string, number>>({});
  const [selectedCollections, setSelectedCollections] = useState<Set<string>>(new Set());
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set());
  const [hoveredCollection, setHoveredCollection] = useState<string | null>(null);
  const FILES_PER_PAGE = 5;

  // 컬렉션 목록 불러오기
  useEffect(() => {
    const fetchCollections = async () => {
      const result = await getCollections();
      console.log(result);
      const list = result.data;
      console.log(list);
      setCollections(list);
    };
    fetchCollections();
  }, []);

  // 보기 버튼 클릭 시 문서 리스트 호출
  const handleViewClick = async (collectionNo: string) => {
    console.log('View clicked for collectionNo:', collectionNo);
    const res = await getDocInCollections(collectionNo);
    console.log(res);
    const docs = res.data;
    console.log(docs);
    setCollections((prev) =>
      prev.map((c) => (c.collectionNo === collectionNo ? { ...c, files: docs } : c))
    );

    setOpen((prev) => ({ ...prev, [collectionNo]: true }));
  };

  // 컬렉션 토글 (선택/해제)
  const toggleSelectCollection = (colNo: string) => {
    setSelectedCollections((prev) => {
      const next = new Set(prev);
      const willSelect = !next.has(colNo);
      if (willSelect) next.add(colNo);
      else next.delete(colNo);

      const col = collections.find((c) => c.collectionNo === colNo);
      if (col && (col as any).files) {
        setSelectedFiles((prevFiles) => {
          const nextFiles = new Set(prevFiles);
          for (const f of (col as any).files as documentDatatype[]) {
            const key = `${colNo}::${f.fileNo}`;
            if (willSelect) nextFiles.add(key);
            else nextFiles.delete(key);
          }
          return nextFiles;
        });
      }
      return next;
    });
  };

  //  파일 선택
  const toggleSelectFile = (colNo: string, fileNo: string) => {
    const key = `${colNo}::${fileNo}`;
    setSelectedFiles((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  // 단일 문서 삭제
  const handleDeleteDoc = async (fileNo: string) => {
    console.log('Deleting fileNo:', fileNo);
    try {
      await deleteDocument(fileNo);

      // 삭제 후 UI 상태 갱신
      setCollections((prev) =>
        prev.map((c) => {
          if (!(c as any).files) return c;
          // 해당 컬렉션 내에서 fileNo 일치하지 않는 것만 남김
          const newFiles = (c as any).files.filter((f: documentDatatype) => f.fileNo !== fileNo);
          return { ...c, files: newFiles };
        })
      );

      toast.success('문서가 삭제되었습니다 ✅');
    } catch (error) {
      toast.error('문서 삭제 중 오류가 발생했습니다.');
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
          <Trash2 size={14} onClick={() => {}} />
          선택 삭제
        </button>
      </div>

      {/* 컬렉션 목록 */}
      {collections.map((col) => {
        const files: documentDatatype[] = Array.isArray((col as any).files)
          ? (col as any).files
          : [];
        const colNo = col.collectionNo;
        const currentPage = page[colNo] || 1;
        const start = (currentPage - 1) * FILES_PER_PAGE;
        const totalFiles = files.length;
        const visibleFiles = files.slice(start, start + FILES_PER_PAGE);

        const totalPages = Math.ceil(totalFiles / FILES_PER_PAGE);

        return (
          <div
            key={colNo}
            onMouseLeave={() => setHoveredCollection((prev) => (prev === colNo ? null : prev))}
            className={
              `border rounded-lg p-3 transition cursor-pointer ` +
              (selectedCollections.has(colNo)
                ? 'bg-[var(--color-hebees-bg)]/40 ring-1 ring-[var(--color-hebees)]'
                : hoveredCollection === colNo
                  ? ''
                  : 'hover:bg-[var(--color-hebees-bg)]/50 hover:ring-1 hover:ring-[var(--color-hebees)]')
            }
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
                    if (open[colNo]) {
                      setOpen((prev) => ({ ...prev, [colNo]: false }));
                    } else {
                      handleViewClick(colNo);
                    }
                  }}
                  className="flex items-center text-sm text-gray-500 hover:text-[var(--color-hebees)] transition"
                >
                  {open[colNo] ? (
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
            {open[colNo] && (
              <>
                <ul className="pl-4 text-xs text-gray-700 space-y-2 mt-2">
                  {visibleFiles.map((file) => (
                    <li
                      key={file.fileNo}
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleSelectFile(colNo, file.fileNo);
                      }}
                      onMouseEnter={() => setHoveredCollection(colNo)}
                      onMouseLeave={() =>
                        setHoveredCollection((prev) => (prev === colNo ? null : prev))
                      }
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

                        {/* 추가 정보 (파일 용량, `저장` 위치, 저장 일시) */}
                        <div className="flex flex-wrap sm:flex-nowrap items-center gap-x-4 gap-y-1 text-gray-500">
                          <span className="whitespace-nowrap"> {file.size} KB</span>
                          <span className="whitespace-nowrap">
                            {collections.find((c) => c.collectionNo === file.collectionNo)?.name ||
                              '알 수 없음'}
                          </span>
                          <span className="whitespace-nowrap">
                            {new Date(file.createdAt).toLocaleString()}
                          </span>
                        </div>
                      </div>

                      {/* 선택 및 삭제 */}
                      <div className="flex items-center gap-2 ml-4">
                        <input
                          type="checkbox"
                          className="accent-[var(--color-hebees)] cursor-pointer"
                          checked={selectedFiles.has(`${colNo}::${file.fileNo}`)}
                          onClick={(e) => e.stopPropagation()}
                          onChange={() => toggleSelectFile(colNo, file.fileNo)}
                        />
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            // handleDeleteFile(colNo, file.fileNo);
                          }}
                          className="text-[var(--color-hebees)] hover:opacity-80 transition"
                        >
                          <Trash2 size={16} onClick={() => handleDeleteDoc(file.fileNo)} />
                        </button>
                      </div>
                    </li>
                  ))}
                </ul>

                {/* 페이지네이션 */}
                {totalPages > 1 && (
                  <div className="flex justify-center gap-2 items-center">
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
