import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import clsx from 'clsx';
import type { Collection } from '@/domains/admin/components/rag-test/types';
import { getDocInCollections } from '@/domains/admin/api/documents.api';
import type { documentDatatype } from '@/domains/admin/types/documents.types';
import { FolderOpen, RefreshCw } from 'lucide-react';
import UploadedFileList from '@/shared/components/file/UploadedFileList';
import { formatCreatedAt } from '@/shared/utils/date';

export type DocItem = {
  id: string;
  name: string;
  sizeKB: number;
  createdAt?: string;
  categoryNo?: string;
  type: string;
  status: string;
};

type Props = {
  collection: Collection;
  onDownload?: (id: string) => void;
  onReindex?: (id: string) => void;
  onDelete?: (ids: string[]) => void;
  onRefresh?: () => void;
  setSelectedDocs?: (docs: DocItem[]) => void;
};

export default function CollectionDocumentsAdm({
  collection,
  onDownload,
  onDelete,
  onRefresh,
  setSelectedDocs,
}: Props) {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [pageNum, setPageNum] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [hasNext, setHasNext] = useState(false);

  const [docsList, setDocsList] = useState<DocItem[]>([]);

  const convertToDocItems = (docs: documentDatatype[]): DocItem[] => {
    return docs.map((doc) => ({
      id: doc.fileNo,
      name: doc.name,
      sizeKB: Number(doc.size) / 1024,
      createdAt: formatCreatedAt(doc.createdAt),
      categoryNo: doc.categoryNo || undefined,
      type: doc.type || 'txt',
      status: doc.status,
    }));
  };

  // 선택된 컬렉션의 문서 쿼리
  const { data: result } = useQuery({
    queryKey: ['docs', collection.id, pageNum],
    queryFn: () => getDocInCollections(collection.id, { pageNum, pageSize: 20 }),
    enabled: !!collection,
  });

  useEffect(() => {
    if (!result) return;

    setTotalPages(result.pagination.totalPages);
    setHasNext(result.pagination.hasNext);

    setDocsList(convertToDocItems(result.data));
    setSelectedDocs?.(convertToDocItems(result.data));
  }, [result]);

  return (
    <div className="rounded-2xl border bg-white p-8 shadow-sm">
      <header className="mb-4 flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <h3 className="text-xl font-bold text-gray-900 mb-2 sm:mb-0">Collection 문서 목록</h3>
        <div className="flex items-center gap-2 flex-wrap">
          <button
            type="button"
            onClick={async () => {
              if (!onRefresh) return;
              setIsRefreshing(true);

              try {
                await Promise.resolve(onRefresh());
              } finally {
                setTimeout(() => setIsRefreshing(false), 300);
              }
            }}
            className={clsx(
              'flex items-center gap-1.5 text-sm rounded-md px-3 py-1',
              'border border-gray-200 text-gray-600 hover:bg-gray-50 hover:text-black transition-colors',
              'disabled:opacity-50 disabled:cursor-not-allowed'
            )}
          >
            <RefreshCw size={16} />
            {isRefreshing ? '불러오는 중...' : '새로고침'}
          </button>
        </div>
      </header>

      <div className="flex items-center justify-between border border-gray-200 p-4 rounded-lg">
        <div className="flex items-center gap-4">
          <div className="flex p-4 items-center justify-center rounded-lg bg-[var(--color-hebees)] text-white">
            <FolderOpen size={24} />
          </div>
          <span className="text-xl font-semibold text-gray-900">{collection.name}</span>
        </div>
      </div>

      <p className="mt-4 mb-2 inline-flex items-center gap-2 rounded-md bg-[var(--color-hebees-bg)] px-3 py-1 text-sm font-normal text-[var(--color-hebees)]">
        <span className="font-bold">TIP</span>
        선택한 문서만 업데이트/다운로드/삭제할 수 있어요.
      </p>

      <UploadedFileList
        docs={docsList}
        onDownload={onDownload}
        pageSize={20}
        onDelete={onDelete}
        brand="hebees"
        showStatus={true}
        pagination={{
          pageNum,
          totalPages,
          hasPrev: pageNum > 1,
          hasNext: hasNext || pageNum < totalPages,
          isLoading: false,
          onPageChange: (newPage: number) => {
            const isNextClick = newPage === pageNum + 1;
            if (newPage < 1) return;
            if (!isNextClick && newPage > totalPages) return;
            if (isNextClick && !(hasNext || pageNum < totalPages)) return;

            setPageNum(newPage);
            window.scrollTo({ top: 0, behavior: 'instant' as ScrollBehavior });
          },
        }}
      />
    </div>
  );
}
