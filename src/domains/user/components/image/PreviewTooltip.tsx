import { createPortal } from 'react-dom';

export interface PreviewTooltipProps {
  url: string | null;
  x: number;
  y: number;
  visible: boolean;
}

export default function PreviewTooltip({ url, x, y, visible }: PreviewTooltipProps) {
  if (!visible || !url) return null;

  // 화면 밖 방지
  const margin = 16;
  const width = 320;
  const height = 200;
  const vw = typeof window !== 'undefined' ? window.innerWidth : 0;
  const vh = typeof window !== 'undefined' ? window.innerHeight : 0;

  const left = Math.min(vw - width - margin, x + 18);
  const top = Math.min(vh - height - margin, y + 18);

  return createPortal(
    <div
      className="fixed z-[9999] rounded-xl shadow-2xl border border-black/10 bg-white/90 backdrop-blur supports-[backdrop-filter]:bg-white/70"
      style={{ left, top, width, height }}
    >
      <img
        src={url}
        alt="preview"
        className="w-full h-full object-contain rounded-xl"
        draggable={false}
      />
    </div>,
    document.body
  );
}
