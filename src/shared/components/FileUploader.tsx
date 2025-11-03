import { useRef, useState } from 'react';
import type { DragEvent } from 'react';
import { UploadCloud } from 'lucide-react';

type Brand = 'hebees' | 'retina';

type Props = {
  onFiles: (files: File[]) => void;
  accept?: string;
  multiple?: boolean;
  maxSizeMB?: number;
  disabled?: boolean;
  className?: string;
  brand?: Brand;
};

export default function FileDropzone({
  onFiles,
  accept = '.pdf,.doc,.docx,.xls,.xlsx,.csv,.txt',
  multiple = true,
  maxSizeMB = 50,
  disabled = false,
  className = '',
  brand = 'hebees',
}: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isOver, setIsOver] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const dragCounterRef = useRef(0);

  const openFileDialog = () => {
    if (!disabled) inputRef.current?.click();
  };

  const handleFiles = (files: FileList | File[]) => {
    const arr = Array.from(files);
    if (!arr.length) return;

    const overs = arr.filter(f => f.size > maxSizeMB * 1024 * 1024);
    if (overs.length) {
      setError(`파일당 최대 ${maxSizeMB}MB까지 업로드할 수 있어요.`);
      return;
    }

    setError(null);
    onFiles(arr);
  };

  const onDragEnter = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (disabled) return;
    dragCounterRef.current += 1;
    setIsOver(true);
  };

  const onDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (disabled) return;
    e.dataTransfer.dropEffect = 'copy';
  };

  const onDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    dragCounterRef.current = Math.max(0, dragCounterRef.current - 1);
    if (dragCounterRef.current === 0) setIsOver(false);
  };

  const onDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (disabled) return;

    dragCounterRef.current = 0;
    setIsOver(false);

    const dt = e.dataTransfer;
    if (dt?.files && dt.files.length > 0) handleFiles(dt.files);
  };

  const base =
    'relative w-full rounded-2xl border-2 border-dashed p-8 sm:p-12 outline-none transition';
  const stateCls = disabled ? 'opacity-60 cursor-not-allowed' : 'cursor-pointer';

  const overCls =
    brand === 'hebees'
      ? 'bg-[var(--color-hebees-bg)] border-[var(--color-hebees)]'
      : 'bg-[var(--color-retina-bg)] border-[var(--color-retina)]';

  const hoverCls =
    brand === 'hebees'
      ? 'hover:bg-[var(--color-hebees-bg)] hover:border-[var(--color-hebees)]'
      : 'hover:bg-[var(--color-retina-bg)] hover:border-[var(--color-retina)]';

  const dropzoneClass = [
    base,
    stateCls,
    isOver ? overCls : 'bg-white border-gray-300/60',
    !isOver && hoverCls,
  ]
    .filter(Boolean)
    .join(' ');

  const buttonBrand =
    brand === 'hebees'
      ? 'bg-[var(--color-hebees)] hover:bg-[var(--color-hebees)] focus-visible:outline-[var(--color-hebees)]'
      : 'bg-[var(--color-retina)] hover:bg-[var(--color-retina)] focus-visible:outline-[var(--color-retina)]';

  const iconBg = brand === 'hebees' ? 'bg-[var(--color-hebees)]' : 'bg-[var(--color-retina)]';

  return (
    <div className={className}>
      <div
        role="button"
        tabIndex={0}
        onClick={openFileDialog}
        onKeyDown={e => (e.key === 'Enter' || e.key === ' ') && openFileDialog()}
        onDragEnter={onDragEnter}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        className={dropzoneClass}
        aria-label="파일 업로드 영역"
      >
        <div className="mx-auto max-w-xl text-center">
          <div
            className={`mx-auto mb-4 flex size-14 items-center justify-center rounded-full ${iconBg} shadow-sm`}
          >
            <UploadCloud className="size-7 text-white" />
          </div>

          <p className="text-sm font-semibold text-gray-800">파일 업로드 후, RAG 챗봇 학습 시작</p>
          <p className="mt-1 text-xs text-gray-500">
            PDF, DOCX, XLSX 파일을 드래그하거나 클릭하여 업로드 하세요.
          </p>

          <div className="mt-4">
            <button
              type="button"
              onClick={openFileDialog}
              disabled={disabled}
              className={`inline-flex items-center rounded-md px-4 py-2 text-sm font-medium text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 disabled:opacity-60 ${buttonBrand}`}
            >
              파일 선택
            </button>
          </div>

          {error && <p className="mt-3 text-xs text-red-600">{error}</p>}
        </div>

        <input
          ref={inputRef}
          type="file"
          accept={accept}
          multiple={multiple}
          disabled={disabled}
          onChange={e => e.target.files && handleFiles(e.target.files)}
          className="sr-only"
        />
      </div>
    </div>
  );
}
