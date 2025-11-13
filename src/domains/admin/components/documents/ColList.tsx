import { useState, useEffect, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  FolderOpen,
  // FileText,
  // ChevronLeft,
  // ChevronRight,
  // ChevronDown,
  // ChevronRight as ChevronRightIcon,
  // Trash2,
  // Download,
} from 'lucide-react';
import { getCollections, getDocInCollections } from '@/domains/admin/api/documents.api';
import type { documentDatatype } from '@/domains/admin/types/documents.types';
// import { deleteFile, downloadFile } from '@/shared/api/file.api';
// import { toast } from 'react-toastify';
import type { Collection } from '@/domains/admin/components/rag-test/types';
import type { DocItem } from '@/domains/admin/components/rag-test/CollectionDocuments';

type ColListProps = {
  onCollectionSelect?: (collection: Collection | null, docs: DocItem[]) => void;
};

export default function ColList({ onCollectionSelect }: ColListProps) {
  // const [open, setOpen] = useState<Record<string, boolean>>({});
  // const [page, setPage] = useState<Record<string, number>>({});
  // const [selectedCollections, setSelectedCollections] = useState<Set<string>>(new Set());
  // const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set());
  // const [hoveredCollection, setHoveredCollection] = useState<string | null>(null);

  // const FILES_PER_PAGE = 5;

  // 컬렉션 목록 조회
  const { data: collectionsResult } = useQuery({
    queryKey: ['collections'],
    queryFn: () => getCollections(),
  });

  const collections = collectionsResult?.data ?? [];
  //  각 컬렉션의 문서 쿼리 (React Query로 병렬 관리) - 현재 사용 안 함
  // const docsQueries = useQueries({
  //   queries: collections.map((col) => ({
  //     queryKey: ['docs', col.collectionNo],
  //     queryFn: () => getDocInCollections(col.collectionNo),
  //     select: (res: { data: unknown }) => {
  //       const d = res.data;
  //       console.log('문서 목록 조회:', d);
  //       if (Array.isArray(d)) return d;
  //       if (Array.isArray((d as { data?: unknown })?.data)) return (d as { data: unknown[] }).data;
  //       if (Array.isArray((d as { items?: unknown })?.items))
  //         return (d as { items: unknown[] }).items;
  //       return []; // 🔥 여기서 보정하는 것이 핵심
  //     },
  //     enabled: !!open[col.collectionNo], // 열린 컬렉션만 API 요청
  //   })),
  // });

  // 보기 버튼 클릭 - 현재 사용 안 함
  // const handleViewClick = (collectionNo: string) => {
  //   setOpen((prev) => ({
  //     ...prev,
  //     [collectionNo]: !prev[collectionNo],
  //   }));
  // };

  // 컬렉션 선택 토글 - 현재 사용 안 함
  // const toggleSelectCollection = (colNo: string) => {
  //   setSelectedCollections((prev) => {
  //     const next = new Set(prev);
  //     const willSelect = !next.has(colNo);
  //     if (willSelect) next.add(colNo);
  //     else next.delete(colNo);
  //     return next;
  //   });
  // };

  // 파일 선택 - 현재 사용 안 함
  // const toggleSelectFile = (colNo: string, fileNo: string) => {
  //   const key = `${colNo}::${fileNo}`;
  //   setSelectedFiles((prev) => {
  //     const next = new Set(prev);
  //     if (next.has(key)) next.delete(key);
  //     else next.add(key);
  //     return next;
  //   });
  // };

  // const queryClient = useQueryClient();

  // // 문서 삭제
  // const handleDeleteDoc = async (fileNo: string, colNo: string) => {
  //   try {
  //     const data = await deleteFile(fileNo);
  //     const isSuccess = data.deleted;
  //     console.log('삭제 성공 여부:', isSuccess);

  //     // 서버에서 실제로 삭제 성공했는지 확인
  //     if (!isSuccess) {
  //       toast.error('서버에서 문서를 삭제하지 못했습니다 ❌');
  //       return;
  //     }

  //     // React Query 캐시 업데이트
  //     const key = ['docs', colNo];
  //     const old = queryClient.getQueryData<documentDatatype[]>(key);

  //     if (Array.isArray(old)) {
  //       queryClient.setQueryData(
  //         key,
  //         old.filter((doc) => doc.fileNo !== fileNo)
  //       );
  //     }

  //     // 항상 최신화 (서버 데이터 동기화)
  //     queryClient.invalidateQueries({ queryKey: key });

  //     toast.success('삭제 완료 ✅');
  //   } catch (error) {
  //     toast.error('삭제 실패 ❌');
  //     console.error('파일 삭제 오류:', error);
  //   }
  // };

  // 문서 다운로드
  // const handleDownloadDoc = async (fileNo: string, fileName: string) => {
  //   console.log(fileNo, '@@', fileName);

  //   try {
  //     const result = await downloadFile(fileNo, {
  //       inline: false,
  //     });
  //     const url = result.data.url;
  //     console.log(fileNo, fileName);

  //     const link = document.createElement('a');
  //     link.href = url;
  //     link.download = fileName;
  //     link.click();
  //   } catch (error) {
  //     toast.error('문서 다운로드 중 오류가 발생했습니다.');
  //     console.log(error);
  //   }
  // };

  // const formatFileSize = (sizeInB: number) => {
  //   const sizeInKB = sizeInB / 1024;
  //   if (sizeInKB >= 1024) {
  //     const sizeInMB = sizeInKB / 1024;
  //     return `${sizeInMB.toFixed(2)} MB`; // 소수점 2자리
  //   }
  //   return `${sizeInKB.toFixed(2)} KB`;
  // };

  // 컬렉션 클릭 핸들러
  const [selectedCollectionForView, setSelectedCollectionForView] = useState<string | null>(null);

  const handleCollectionClick = (collectionNo: string) => {
    const newSelection = selectedCollectionForView === collectionNo ? null : collectionNo;
    setSelectedCollectionForView(newSelection);
  };

  // 선택된 컬렉션 정보
  const selectedCollectionData = useMemo(() => {
    if (!selectedCollectionForView) return null;
    const col = collections.find((c) => c.collectionNo === selectedCollectionForView);
    if (!col) return null;
    return {
      id: col.collectionNo,
      name: col.name,
      ingestTemplate: col.ingestGroupNo || undefined,
    } as Collection;
  }, [selectedCollectionForView, collections]);

  // 선택된 컬렉션의 문서 쿼리
  const { data: selectedCollectionDocsData } = useQuery({
    queryKey: ['docs', selectedCollectionForView],
    queryFn: () => getDocInCollections(selectedCollectionForView!),
    select: (res: { data: unknown }) => {
      const d = res.data;
      if (Array.isArray(d)) return d;
      if (Array.isArray((d as { data?: unknown })?.data)) return (d as { data: unknown[] }).data;
      if (Array.isArray((d as { items?: unknown })?.items))
        return (d as { items: unknown[] }).items;
      return [];
    },
    enabled: !!selectedCollectionForView,
  });

  // documentDatatype을 DocItem으로 변환
  const convertToDocItems = (docs: documentDatatype[]): DocItem[] => {
    return docs.map((doc) => ({
      id: doc.fileNo,
      name: doc.name,
      sizeKB: Number(doc.size) / 1024,
      createdAt: doc.createdAt,
      categoryNo: doc.categoryNo || undefined,
      type: doc.type || 'txt',
    }));
  };

  const selectedCollectionDocs = useMemo(() => {
    if (!selectedCollectionDocsData) return [];
    return convertToDocItems(selectedCollectionDocsData);
  }, [selectedCollectionDocsData]);

  // 부모 컴포넌트에 선택된 컬렉션 정보 전달
  useEffect(() => {
    if (onCollectionSelect) {
      onCollectionSelect(selectedCollectionData, selectedCollectionDocs);
    }
  }, [selectedCollectionData, selectedCollectionDocs, onCollectionSelect]);

  return (
    <section className="flex flex-col w-full rounded-xl border-gray-200 bg-white box-border space-y-3 flex-shrink-0 [scrollbar-gutter:stable]">
      {/* 컬렉션 목록 */}
      {collections.map((col) => {
        const colNo = col.collectionNo;
        // const docsQuery = docsQueries[index];
        // const docs = docsQuery?.data || [];
        // const isDocsLoading = docsQuery?.isLoading;

        // const currentPage = page[colNo] || 1;
        // const start = (currentPage - 1) * FILES_PER_PAGE;
        // const totalFiles = docs.length;
        // const visibleFiles = docs.slice(start, start + FILES_PER_PAGE);
        // const totalPages = Math.ceil(totalFiles / FILES_PER_PAGE);

        return (
          <div
            key={colNo}
            onClick={() => handleCollectionClick(colNo)}
            // onMouseLeave={() => setHoveredCollection((prev) => (prev === colNo ? null : prev))}
            className={`border rounded-lg p-3 transition cursor-pointer ${
              selectedCollectionForView === colNo
                ? 'bg-[var(--color-hebees-bg)] ring-2 ring-[var(--color-hebees)]'
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
            </div>
          </div>
        );
      })}
    </section>
  );
}
