import { useEffect, useRef } from 'react';
import { Download, Copy, RefreshCw, Loader2, Plus } from 'lucide-react';
import Tooltip from '@/shared/components/Tooltip';
import type { GenSize, StylePreset } from '@/domains/user/types/image.type';

type Props = {
  images: string[];
  loading: boolean;
  style: StylePreset;
  size: GenSize;
  onDownload: (src: string, idx: number) => void;
  onCopy: (src: string) => void;
  onRegenerate: () => void;
};

export default function ImageResultPane({
  images,
  loading,
  style,
  size,
  onDownload,
  onCopy,
  onRegenerate,
}: Props) {
  const rightPaneRef = useRef<HTMLDivElement>(null);

  // 새 이미지가 오면 상단으로 스크롤
  useEffect(() => {
    if (images.length > 0) {
      rightPaneRef.current?.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }, [images.length]);

  return (
    <div
      ref={rightPaneRef}
      className="min-h-[60vh] rounded-xl border bg-white p-8 overflow-auto no-scrollbar"
    >
      {loading && images.length === 0 && (
        <div className="flex items-center justify-center h-full min-h-[400px]">
          <div className="aspect-square w-96 animate-pulse rounded-lg bg-gray-100" />
        </div>
      )}

      {!loading && images.length === 0 && (
        <div className="h-full min-h-[420px] flex flex-col items-center justify-center text-center text-gray-600">
          <div className="mb-2 text-lg font-semibold">이미지를 생성해 보세요</div>
          <div className="text-sm">
            프롬프트를 입력하고 옵션을 선택한 뒤 &ldquo;이미지 생성하기&rdquo;를 눌러요.
          </div>
          <div className="mt-6 inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs text-gray-500">
            <Plus size={14} /> 예: &ldquo;포근한 크리스마스 분위기의 일러스트, 눈 내리는 마을,
            트리와 선물 상자, 따뜻한 조명, 포스터 스타일&rdquo;
          </div>
        </div>
      )}

      {images.length > 0 && (
        <div className="flex flex-col items-center justify-center w-full">
          <figure className="relative w-[350px] md:w-[420px] mb-4">
            <img
              src={images[0]}
              alt="생성 이미지"
              className="aspect-square w-full rounded-lg object-cover border"
              loading="lazy"
            />

            {/* 옵션 뱃지 — 우측 하단 고정 */}
            <div className="absolute right-2 bottom-2 rounded-md bg-black/60 px-2 py-1 text-[10px] text-white backdrop-blur-sm">
              {style} · {size}
            </div>
          </figure>

          {/* 이미지 아래 고정 버튼 바 */}
          <div className="flex gap-2 sticky bottom-0 bg-white py-3 w-full max-w-[420px] justify-center border-t">
            <Tooltip content="다운로드" side="bottom">
              <button
                onClick={() => onDownload(images[0], 0)}
                className="rounded-md bg-gray-100 px-3 py-2 text-xs hover:bg-gray-200"
              >
                <Download size={16} />
              </button>
            </Tooltip>

            <Tooltip content="이미지 복사" side="bottom">
              <button
                onClick={() => onCopy(images[0])}
                className="rounded-md bg-gray-100 px-3 py-2 text-xs hover:bg-gray-200"
              >
                <Copy size={16} />
              </button>
            </Tooltip>

            <Tooltip content="다시 생성" side="bottom">
              <button
                onClick={onRegenerate}
                className="rounded-md bg-[var(--color-retina)] text-white px-3 py-2 text-xs hover:opacity-90"
              >
                {loading ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={16} />}
              </button>
            </Tooltip>
          </div>
        </div>
      )}
    </div>
  );
}
