import { useState, useEffect, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { FolderOpen } from 'lucide-react';
import { getCollections } from '@/domains/admin/api/documents.api';
import type { Collection } from '@/domains/admin/components/rag-test/types';

type ColListProps = {
  onCollectionSelect?: (collection: Collection | null) => void;
};

export default function ColList({ onCollectionSelect }: ColListProps) {
  // 컬렉션 목록 조회
  const { data: collectionsResult, isLoading } = useQuery({
    queryKey: ['collections'],
    queryFn: () => getCollections(),
  });

  const collections = collectionsResult?.data ?? [];

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

  // // 선택된 컬렉션의 문서 쿼리
  // const { data: selectedCollectionDocsData } = useQuery({
  //   queryKey: ['docs', selectedCollectionForView],
  //   queryFn: () => getDocInCollections(selectedCollectionForView!),
  //   select: (res: { data: unknown }) => {
  //     const d = res.data;
  //     if (Array.isArray(d)) return d;
  //     if (Array.isArray((d as { data?: unknown })?.data)) return (d as { data: unknown[] }).data;
  //     if (Array.isArray((d as { items?: unknown })?.items))
  //       return (d as { items: unknown[] }).items;
  //     return [];
  //   },
  //   enabled: !!selectedCollectionForView,
  // });

  // 부모 컴포넌트에 선택된 컬렉션 정보 전달
  useEffect(() => {
    if (onCollectionSelect) {
      onCollectionSelect(selectedCollectionData);
    }
  }, [selectedCollectionData, onCollectionSelect]);

  return (
    <section className="flex flex-col w-full rounded-xl border-gray-200 bg-white box-border space-y-3 flex-shrink-0 [scrollbar-gutter:stable]">
      {isLoading && (
        <div className="animate-pulse space-y-3 py-4">
          <div className="h-12 bg-gray-200 rounded-lg"></div>
          <div className="h-12 bg-gray-200 rounded-lg"></div>
          <div className="h-12 bg-gray-200 rounded-lg"></div>
          <div className="h-12 bg-gray-200 rounded-lg"></div>
        </div>
      )}
      {/* 컬렉션 목록 */}
      {collections.map((col) => {
        const colNo = col.collectionNo;
        return (
          <div
            key={colNo}
            onClick={() => handleCollectionClick(colNo)}
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
