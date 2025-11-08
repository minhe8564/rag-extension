import { useEffect, useMemo, useRef, useState, type DragEvent } from 'react';
import { UploadCloud } from 'lucide-react';
import { getCategories } from '@/shared/api/file.api';
import { useCategoryStore } from '@/shared/store/categoryMap';

type Brand = 'hebees' | 'retina';
type CategoryId = string;

type Props = {
  onUpload: (payload: { files: File[]; category: CategoryId }) => void;
  accept?: string;
  multiple?: boolean;
  maxSizeMB?: number;
  disabled?: boolean;
  className?: string;
  brand?: Brand;
  defaultCategory?: string;
};

type ServerCategory = { categoryNo: string; name: string };

const parseAccept = (accept: string) => {
  const tokens = accept
    .split(',')
    .map((t) => t.trim())
    .filter(Boolean);
  const exts = tokens.filter((t) => t.startsWith('.')).map((t) => t.toLowerCase());
  const mimes = tokens.filter((t) => t.includes('/')).map((t) => t.toLowerCase());
  return { exts, mimes };
};

const matchMime = (fileType: string, mimes: string[]) => {
  if (!fileType) return false;
  const [ft, fs] = fileType.toLowerCase().split('/');
  return mimes.some((m) => {
    const [mt, ms] = m.split('/');
    return (mt === '*' || mt === ft) && (ms === '*' || ms === fs);
  });
};

export default function FileDropzone({
  onUpload,
  accept = '.pdf,.md,.doc,.docx,.xlsx',
  multiple = true,
  maxSizeMB = 100,
  disabled = false,
  className = '',
  brand = 'hebees',
  defaultCategory = '기타',
}: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const dragCounterRef = useRef(0);

  const categoryList = useCategoryStore((s) => s.categoryList);
  const categoryMap = useCategoryStore((s) => s.categoryMap);
  const setCategories = useCategoryStore((s) => s.setCategories);

  const [categoryId, setCategoryId] = useState<CategoryId>('');
  const [isOver, setIsOver] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const acceptRule = useMemo(() => parseAccept(accept), [accept]);
  const allowLabel = useMemo(() => {
    const rule = [...acceptRule.exts, ...acceptRule.mimes].join(', ');
    return rule || accept;
  }, [acceptRule, accept]);

  useEffect(() => {
    let active = true;
    if (categoryList.length > 0) return;
    (async () => {
      const res = await getCategories();
      const list = (res.data?.result?.data ?? res.data?.result ?? []) as ServerCategory[];
      if (!active) return;
      setCategories(list);
    })();
    return () => {
      active = false;
    };
  }, [categoryList.length, setCategories]);

  const nameById = (id?: string) => (id ? (categoryMap[id] ?? '') : '');

  useEffect(() => {
    if (!categoryList.length) return;
    const exists = categoryList.some((c) => c.id === categoryId);
    if (exists && categoryId) return;
    const byName = categoryList.find((c) => c.name === defaultCategory)?.id;
    const fallback = byName ?? categoryList[0]?.id ?? '';
    if (fallback) setCategoryId(fallback);
  }, [categoryList, defaultCategory, categoryId]);

  const openFileDialog = () => {
    if (!disabled) inputRef.current?.click();
  };

  const isAllowedFile = (file: File) => {
    const name = file.name || '';
    const ext = '.' + (name.split('.').pop() || '').toLowerCase();
    const hasExtRule = acceptRule.exts.length > 0;
    const hasMimeRule = acceptRule.mimes.length > 0;
    const extOk = !hasExtRule || acceptRule.exts.includes(ext);
    const mimeOk = !hasMimeRule || matchMime(file.type, acceptRule.mimes);
    if (!hasExtRule && !hasMimeRule) return true;
    return (hasExtRule && extOk) || (hasMimeRule && mimeOk);
  };

  const handleFiles = (files: FileList | File[]) => {
    let arr = Array.from(files);
    if (!arr.length) return;
    if (!multiple && arr.length > 1) arr = [arr[0]];

    const overs = arr.filter((f) => f.size > maxSizeMB * 1024 * 1024);
    if (overs.length) {
      setError(`파일당 최대 ${maxSizeMB}MB까지 업로드할 수 있어요.`);
      return;
    }

    const invalid = arr.filter((f) => !isAllowedFile(f));
    if (invalid.length) {
      setError(
        `허용되지 않는 파일 형식이에요: ${invalid.map((f) => f.name).join(', ')}\n가능한 형식: ${allowLabel}`
      );
      return;
    }

    if (!categoryId) {
      setError('카테고리를 먼저 선택해주세요.');
      return;
    }

    setError(null);
    onUpload({ files: arr, category: categoryId });
  };

  const onDragEnter = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (disabled) return;
    dragCounterRef.current += 1;
    setIsOver(true);
  };

  const onDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (!disabled) e.dataTransfer.dropEffect = 'copy';
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

  const pillActive =
    brand === 'hebees'
      ? 'bg-[var(--color-hebees)] text-white border-[var(--color-hebees)]'
      : 'bg-[var(--color-retina)] text-white border-[var(--color-retina)]';

  return (
    <div className={className}>
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <div className="flex flex-wrap gap-1.5">
          {categoryList.map((c) => {
            const active = c.id === categoryId;
            return (
              <button
                key={c.id}
                type="button"
                onClick={() => setCategoryId(c.id)}
                className={[
                  'rounded-full border px-3 py-1.5 text-xs',
                  'transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2',
                  active ? pillActive : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50',
                ].join(' ')}
                aria-pressed={active}
              >
                {c.name}
              </button>
            );
          })}
        </div>
      </div>

      <div
        role="button"
        tabIndex={0}
        onClick={openFileDialog}
        onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && openFileDialog()}
        onDragEnter={onDragEnter}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        className={dropzoneClass}
        aria-label="파일 업로드 영역"
        aria-description={`현재 선택된 카테고리: ${nameById(categoryId) || '없음'}`}
      >
        <div className="mx-auto max-w-xl text-center">
          <div
            className={`mx-auto mb-4 flex size-14 items-center justify-center rounded-full ${iconBg} shadow-sm`}
          >
            <UploadCloud className="size-7 text-white" />
          </div>
          <p className="text-sm font-semibold text-gray-800">파일 업로드 후, RAG 챗봇 학습 시작</p>
          <p className="mt-1 text-xs text-gray-500">
            PDF, Markdown, Word, Excel 파일을 드래그하거나 클릭하여 업로드 하세요.
          </p>
          <p className="mt-2 text-xs">
            <span className="text-gray-500">선택된 카테고리:</span>{' '}
            <span className="font-medium text-gray-800">{nameById(categoryId) || '없음'}</span>
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
          {error && <p className="mt-3 whitespace-pre-line text-xs text-red-600">{error}</p>}
        </div>

        <input
          ref={inputRef}
          type="file"
          accept={accept}
          multiple={multiple}
          disabled={disabled}
          onChange={(e) => e.target.files && handleFiles(e.target.files)}
          className="sr-only"
        />
      </div>
    </div>
  );
}
