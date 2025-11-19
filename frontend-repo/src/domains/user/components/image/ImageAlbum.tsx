import { useEffect, useState } from 'react';
import ImageModal from '@/domains/user/components/image/ImageModal';
import PreviewTooltip from '@/domains/user/components/image/PreviewTooltip';
import { getUserImages, deleteImage } from '@/domains/user/api/image.api';
import type { GeneratedImage } from '@/domains/user/types/image.type';
import { Loader2, ImageOff, Maximize2, Trash2 } from 'lucide-react';
import { toast } from 'react-toastify';
import ConfirmModal from '@/shared/components/ConfirmModal';

export default function ImageAlbum() {
  const [images, setImages] = useState<GeneratedImage[]>([]);
  const [loading, setLoading] = useState(true);
  const [hoverUrl, setHoverUrl] = useState<string | null>(null);
  const [mouse, setMouse] = useState({ x: 0, y: 0 });
  const [isHovering, setIsHovering] = useState(false);
  const [openId, setOpenId] = useState<string | null>(null);
  const [openFallbackUrl, setOpenFallbackUrl] = useState<string | undefined>(undefined);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [pendingDeleteId, setPendingDeleteId] = useState<string | null>(null);

  useEffect(() => {
    const fetchImages = async () => {
      try {
        const result = await getUserImages();
        setImages(result);
      } catch (error) {
        console.error(error);
      } finally {
        setLoading(false);
      }
    };
    fetchImages();
  }, []);

  const onCardMouseEnter = (url: string) => {
    setHoverUrl(url);
    setIsHovering(true);
  };
  const onCardMouseLeave = () => {
    setIsHovering(false);
    setHoverUrl(null);
  };
  const onMouseMove = (e: React.MouseEvent) => {
    setMouse({ x: e.clientX, y: e.clientY });
  };

  const openModal = (imageId: string, fallbackUrl?: string) => {
    setOpenId(imageId);
    setOpenFallbackUrl(fallbackUrl);
  };

  const askDelete = (imageId: string) => {
    setPendingDeleteId(imageId);
    setConfirmOpen(true);
  };

  const handleConfirmDelete = async () => {
    if (!pendingDeleteId) return;

    const imageId = pendingDeleteId;
    setConfirmOpen(false);
    setPendingDeleteId(null);

    setDeletingId(imageId);

    const prev = images;
    setImages((arr) => arr.filter((i) => i.image_id !== imageId));

    try {
      const ok = await deleteImage(imageId);
      if (!ok) throw new Error('삭제 실패');
      toast.success(`이미지가 삭제되었습니다.`);
    } catch {
      setImages(prev);
      toast.error('삭제에 실패했습니다. 잠시 후 다시 시도해 주세요.');
    } finally {
      setDeletingId(null);
    }
  };

  if (loading)
    return (
      <div className="flex items-center justify-center py-10 text-gray-500">
        <Loader2 size={18} className="animate-spin mr-2" />
        이미지를 불러오는 중입니다...
      </div>
    );

  if (images.length === 0)
    return (
      <div className="p-6">
        <div className="flex flex-col items-center justify-center py-10 text-gray-400">
          <ImageOff size={40} strokeWidth={1.6} className="mb-3" />
          <p className="text-sm">생성한 이미지가 없습니다.</p>
        </div>
      </div>
    );

  return (
    <div className="rounded-xl border bg-white p-6 shadow-sm mt-6">
      <div
        className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4 z-0"
        onMouseMove={onMouseMove}
      >
        {images.map((img) => (
          <div
            key={img.image_id}
            className="group relative overflow-hidden rounded-xl border bg-white shadow-sm hover:shadow-md transition-shadow duration-200"
            onMouseEnter={() => onCardMouseEnter(img.url)}
            onMouseLeave={onCardMouseLeave}
          >
            <img
              src={img.url}
              alt={img.image_id}
              className="w-full h-40 object-cover rounded-2xl"
              draggable={false}
              onClick={() => openModal(img.image_id, img.url)}
            />

            <div className="absolute bottom-2 right-2 bg-black/60 text-white text-xs px-2 py-0.5 rounded-md">
              {img.type}
            </div>

            <div className="absolute right-2 top-2 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
              <button
                className="rounded-full bg-white/90 backdrop-blur p-2 shadow hover:bg-white"
                onClick={(e) => {
                  e.stopPropagation();
                  openModal(img.image_id, img.url);
                }}
                title="확대 보기"
              >
                <Maximize2 size={16} />
              </button>

              <button
                className="rounded-full bg-white/90 backdrop-blur p-2 shadow hover:bg-white disabled:opacity-50"
                onClick={(e) => {
                  e.stopPropagation();
                  askDelete(img.image_id);
                }}
                disabled={deletingId === img.image_id}
                title="삭제"
              >
                {deletingId === img.image_id ? (
                  <Loader2 size={16} className="animate-spin" />
                ) : (
                  <Trash2 size={16} />
                )}
              </button>
            </div>
          </div>
        ))}
      </div>

      <PreviewTooltip url={hoverUrl} x={mouse.x} y={mouse.y} visible={isHovering} />

      <ImageModal
        open={!!openId}
        onClose={() => setOpenId(null)}
        imageId={openId}
        fallbackUrl={openFallbackUrl}
      />

      <ConfirmModal
        open={confirmOpen}
        onClose={() => setConfirmOpen(false)}
        onConfirm={handleConfirmDelete}
        title="이미지 삭제"
        message={`정말 삭제할까요?\n"[ImageId] ${pendingDeleteId ?? ''}"`}
        confirmText="삭제"
        cancelText="취소"
        variant="danger"
      />
    </div>
  );
}
