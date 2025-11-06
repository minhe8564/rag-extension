import { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { X, Loader2, Download, Copy } from 'lucide-react';
import { getImageDetail } from '@/domains/user/api/image.api';
import { toast } from 'react-toastify';

interface ImageModalProps {
  open: boolean;
  onClose: () => void;
  imageId: string | null;
  fallbackUrl?: string;
}

function pickImageFields(res: unknown): { url: string | null; type: string | null } {
  let url: string | null = null;
  let type: string | null = null;

  if (typeof res === 'object' && res !== null) {
    const r = res as Record<string, unknown>;

    const imageVal = r['image'];
    if (typeof imageVal === 'object' && imageVal !== null) {
      const imageObj = imageVal as Record<string, unknown>;
      const u = imageObj['url'];
      if (typeof u === 'string') url = u;
    }

    if (url === null) {
      const u2 = r['url'];
      if (typeof u2 === 'string') url = u2;
    }

    const t = r['type'];
    if (typeof t === 'string') type = t;
  }

  return { url, type };
}

export default function ImageModal({ open, onClose, imageId, fallbackUrl }: ImageModalProps) {
  const [loading, setLoading] = useState(false);
  const [detailUrl, setDetailUrl] = useState<string | null>(null);
  const [type, setType] = useState<string | null>(null);

  const src = detailUrl ?? fallbackUrl ?? null;

  useEffect(() => {
    if (!open || !imageId) return;
    let alive = true;
    setLoading(true);

    (async () => {
      try {
        const res = await getImageDetail(imageId);
        if (!alive) return;
        const { url, type } = pickImageFields(res);
        setDetailUrl(url ?? fallbackUrl ?? null);
        setType(type);
      } catch {
        setDetailUrl(fallbackUrl ?? null);
      } finally {
        if (alive) setLoading(false);
      }
    })();

    return () => {
      alive = false;
    };
  }, [open, imageId, fallbackUrl]);

  useEffect(() => {
    if (!open) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [open, onClose]);

  if (!open) return null;

  const handleOverlayClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) onClose();
  };

  const handleDownload = async () => {
    if (!src) return;
    try {
      const resp = await fetch(src, { mode: 'cors' });
      const blob = await resp.blob();
      const objectUrl = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = objectUrl;
      a.download = `image-${imageId ?? 'download'}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(objectUrl);
    } catch {
      window.open(src, '_blank', 'noopener,noreferrer');
    }
  };

  return createPortal(
    <div
      className="fixed inset-0 z-[9998] bg-black/60 flex items-center justify-center p-4"
      onClick={handleOverlayClick}
      role="dialog"
      aria-modal="true"
    >
      <div className="relative max-w-5xl w-full rounded-2xl bg-white shadow-2xl overflow-hidden">
        <div className="flex items-center justify-between px-5 pt-4 pb-3">
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-700 font-medium">{type ?? '이미지'}</span>
          </div>

          <div className="flex items-center gap-2">
            {src && !loading && (
              <>
                <button
                  onClick={handleDownload}
                  type="button"
                  className="inline-flex items-center gap-1.5 rounded-full bg-gray-100 hover:bg-gray-200 px-3 py-1.5 text-xs text-gray-700 transition border border-gray-200"
                  title="저장"
                  aria-label="저장"
                >
                  <Download size={14} />
                  저장
                </button>

                <button
                  onClick={() => {
                    navigator.clipboard.writeText(src);
                    toast.success('이미지가 복사되었습니다.');
                  }}
                  type="button"
                  className="inline-flex items-center gap-1.5 rounded-full bg-gray-100 hover:bg-gray-200 px-3 py-1.5 text-xs text-gray-700 transition border border-gray-200"
                  title="복사"
                  aria-label="복사"
                >
                  <Copy size={14} />
                  복사
                </button>
              </>
            )}

            <button
              onClick={onClose}
              className="ml-1 p-2 rounded-full bg-black/5 hover:bg-black/10 transition"
              aria-label="닫기"
              type="button"
            >
              <X size={18} />
            </button>
          </div>
        </div>

        <div className="px-5 pb-5">
          <div className="aspect-video w-full rounded-xl bg-gray-50 border overflow-hidden flex items-center justify-center">
            {loading ? (
              <div className="flex items-center gap-2 text-gray-500">
                <Loader2 className="animate-spin" size={18} />
                고해상도 이미지를 불러오는 중…
              </div>
            ) : src ? (
              <img
                src={src}
                alt={imageId ?? ''}
                className="w-full h-full object-contain select-none"
                draggable={false}
              />
            ) : (
              <div className="text-gray-400">이미지를 표시할 수 없어요.</div>
            )}
          </div>
        </div>
      </div>
    </div>,
    document.body
  );
}
