import { useEffect, useMemo, useRef, useState } from 'react';
import clsx from 'clsx';
import { fetchMyDocumentsNormalized, getPresignedUrl, deleteFile } from '@/shared/api/file.api';
import type { MyDoc } from '@/shared/types/file.types';
import UploadedFileList from '@/shared/components/file/UploadedFileList';
import type { UploadedDoc } from '@/shared/types/file.types';
import { RefreshCw } from 'lucide-react';
import { toast } from 'react-toastify';
import ConfirmModal from '@/shared/components/ConfirmModal';
import { formatCreatedAt } from '@/shared/utils/date';
import { Loader2 } from 'lucide-react';

export default function MyDocsTab() {
  const [myDocs, setMyDocs] = useState<MyDoc[]>([]);
  const [pageNum, setPageNum] = useState(() => {
    const q = new URLSearchParams(window.location.search);
    const p = Number(q.get('p') ?? '1');
    return Number.isFinite(p) && p > 0 ? p : 1;
  });
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [hasNext, setHasNext] = useState(false);
  const [loading, setLoading] = useState(false);
  const [refreshTick, setRefreshTick] = useState(0);
  const [deleting, setDeleting] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [pendingDelete, setPendingDelete] = useState<{ fileNo: string; name?: string } | null>(
    null
  );

  const reqSeq = useRef(0);

  useEffect(() => {
    let active = true;
    const myReqId = ++reqSeq.current;

    (async () => {
      setLoading(true);
      try {
        const { items, total, totalPages, hasNext } = await fetchMyDocumentsNormalized({
          pageNum,
          pageSize: 20,
        });
        if (!active || myReqId !== reqSeq.current) return;

        setMyDocs(items);

        setTotal(total);
        setTotalPages(Math.max(1, totalPages));
        setHasNext(hasNext);
      } finally {
        if (active && myReqId === reqSeq.current) setLoading(false);
      }
    })();

    const url = new URL(window.location.href);
    url.searchParams.set('p', String(pageNum));
    window.history.replaceState({}, '', url);

    return () => {
      active = false;
    };
  }, [pageNum, refreshTick]);

  const uploadedDocs: UploadedDoc[] = useMemo(
    () =>
      myDocs.map((d) => ({
        id: d.fileNo,
        fileNo: d.fileNo,
        name: d.name,
        sizeKB: d.sizeKB,
        createdAt: formatCreatedAt(d.createdAt),
        category: d.bucket ?? '기타',
        categoryId: d.categoryNo != null ? String(d.categoryNo) : undefined,
        type: typeof d.type === 'string' ? d.type : 'txt',
        status: d.status ?? undefined,
      })),
    [myDocs]
  );

  const handleDownload = async (fileNo: string) => {
    const doc = myDocs.find((m) => m.fileNo === fileNo);
    const fallbackName = doc?.name || `${fileNo}.bin`;

    try {
      const signedUrl = await getPresignedUrl(fileNo, { inline: false });
      const res = await fetch(signedUrl);
      if (!res.ok) throw new Error('Failed to fetch file');

      const blob = await res.blob();
      const blobUrl = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = blobUrl;
      a.download = fallbackName;
      a.style.display = 'none';
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(blobUrl);
    } catch (error) {
      console.error('File download failed:', error);
      const signedUrl = await getPresignedUrl(fileNo, { inline: false });
      window.open(signedUrl, '_blank');
    }
  };

  const requestDelete = (ids: string[]) => {
    const fileNo = Array.isArray(ids) ? ids[0] : undefined;
    if (!fileNo) return;

    const target = myDocs.find((d) => d.fileNo === fileNo);
    setPendingDelete({ fileNo, name: target?.name });
    setConfirmOpen(true);
  };

  const confirmDelete = async () => {
    if (!pendingDelete?.fileNo) return;

    try {
      setDeleting(true);
      const res = await deleteFile(pendingDelete.fileNo);

      if (res?.deleted) {
        toast.success('문서를 삭제했어요.');

        setMyDocs((prev) => prev.filter((d) => d.fileNo !== pendingDelete.fileNo));
        setTotal((t) => Math.max(0, t - 1));

        setTimeout(() => {
          const afterCount = myDocs.length - 1;
          if (afterCount === 0 && pageNum > 1) {
            setPageNum((p) => Math.max(1, p - 1));
            setRefreshTick((t) => t + 1);
          }
        }, 0);
      } else {
        toast.error('삭제에 실패했습니다.');
      }
    } catch (e) {
      console.error(e);
    } finally {
      setDeleting(false);
      setConfirmOpen(false);
      setPendingDelete(null);
    }
  };

  const closeConfirm = () => {
    if (deleting) return;
    setConfirmOpen(false);
    setPendingDelete(null);
  };

  return (
    <div className="mt-2">
      <div className="rounded-xl bg-white/95 p-4">
        <div className="mb-3 flex items-center justify-between">
          <p className="text-sm text-gray-600">
            총 <span className="font-medium">{total || '—'}</span>개 문서
          </p>

          <button
            type="button"
            onClick={() => setRefreshTick((t) => t + 1)}
            disabled={loading || deleting}
            className={clsx(
              'flex items-center gap-1.5 text-sm rounded-md px-3 py-1',
              'border border-gray-200 text-gray-600 hover:bg-gray-50 hover:text-black transition-colors',
              'disabled:opacity-50 disabled:cursor-not-allowed'
            )}
          >
            <RefreshCw
              size={16}
              className={clsx((loading || deleting) && 'animate-spin text-gray-400')}
            />
            {loading ? '불러오는 중...' : deleting ? '삭제 중...' : '새로고침'}
          </button>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-8 text-gray-500">
            <Loader2 size={18} className="mr-2 animate-spin" />
            불러오는 중…
          </div>
        ) : (
          <UploadedFileList
            docs={uploadedDocs}
            pageSize={20}
            brand="retina"
            onDownload={handleDownload}
            onDelete={requestDelete}
            showStatus={true}
            pagination={{
              pageNum,
              totalPages,
              hasPrev: pageNum > 1,
              hasNext: hasNext || pageNum < totalPages,
              isLoading: loading || deleting,
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
        )}
      </div>

      <ConfirmModal
        open={confirmOpen}
        onClose={closeConfirm}
        onConfirm={confirmDelete}
        title="문서 삭제"
        message={
          pendingDelete?.name
            ? `정말 이 문서를 삭제할까요?\n"${pendingDelete.name}"`
            : '정말 삭제할까요?'
        }
        confirmText={deleting ? '삭제 중...' : '삭제'}
        cancelText="취소"
        variant="danger"
        zIndex={10080}
      />
    </div>
  );
}
