import { Sparkles, Loader2, Wand2 } from 'lucide-react';
import Tooltip from '@/shared/components/Tooltip';
import type { StylePreset } from '@/domains/user/types/image.type';
import { STYLE_LABEL } from '@/domains/user/types/image.type';

type Brand = 'retina' | 'hebees';

type Props = {
  prompt: string;
  setPrompt: (v: string) => void;
  size: string;
  setSize: (v: string) => void;
  style: StylePreset;
  setStyle: (v: StylePreset) => void;
  loading: boolean;
  disabled: boolean;
  maxLen: number;
  onGenerate: () => void;
  onReusePrompt: (addition?: string) => void;
  brand?: Brand;
};

const brandColors: Record<Brand, { color: string; bg: string }> = {
  retina: {
    color: 'var(--color-retina)',
    bg: 'var(--color-retina-bg)',
  },
  hebees: {
    color: 'var(--color-hebees)',
    bg: 'var(--color-hebees-bg)',
  },
};

export default function ImageGeneratorForm({
  prompt,
  setPrompt,
  size,
  setSize,
  style,
  setStyle,
  loading,
  disabled,
  maxLen,
  onGenerate,
  onReusePrompt,
  brand = 'retina',
}: Props) {
  const chars = prompt.length;

  const colors = brandColors[brand];

  const cssVars: Record<`--${string}`, string> = {
    '--color-primary': colors.color,
    '--color-primary-bg': colors.bg,
  };

  return (
    <div className="rounded-xl border bg-white p-8" style={cssVars}>
      <div className="mb-6 space-y-2">
        <div className="text-xl font-semibold text-black">이미지 설명</div>
        <div className="text-base text-gray-500">
          자세히 설명할수록 좋은 이미지를 만들 수 있어요!
        </div>
      </div>

      <div className="relative">
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value.slice(0, maxLen))}
          className="
            w-full h-40 resize-none rounded-md p-4 text-sm
            bg-[var(--color-primary-bg)]
            border-none outline-none
            focus:ring-1 focus:ring-[var(--color-primary)]
          "
          placeholder='예: "포근한 크리스마스 분위기의 일러스트..."'
        />
        <div className="absolute bottom-4 right-4 text-sm text-gray-400">
          {chars}/{maxLen}
        </div>
      </div>

      <div className="mt-6 grid grid-cols-2 gap-3">
        <div>
          <label className="block text-sm text-gray-500 mb-2">사이즈</label>
          <select
            value={size}
            onChange={(e) => setSize(e.target.value as string)}
            className="w-full rounded-md border px-2 py-2 text-sm"
          >
            <option value="1024x1024">1024 × 1024 (정사각형)</option>
            <option value="832x1248">832 × 1248 (세로)</option>
            <option value="1248x832">1248 × 832 (가로)</option>
            <option value="864x1184">864 × 1184 (세로)</option>
            <option value="1184x864">1184 × 864 (가로)</option>
            <option value="896x1152">896 × 1152 (세로)</option>
            <option value="1152x896">1152 × 896 (가로)</option>
            <option value="768x1344">768 × 1344 (세로)</option>
            <option value="1344x768">1344 × 768 (가로)</option>
            <option value="1536x672">1536 × 672 (와이드)</option>
          </select>
        </div>
      </div>

      <div className="mt-6">
        <label className="block text-sm text-gray-500 mb-3">스타일 프리셋</label>
        <div className="flex flex-wrap gap-2">
          {(Object.keys(STYLE_LABEL) as StylePreset[]).map((k) => {
            const active = k === style;
            return (
              <button
                key={k}
                onClick={() => setStyle(k)}
                className={
                  'rounded-full px-3 py-1.5 text-sm border ' +
                  (active
                    ? 'border-[var(--color-primary)] bg-[var(--color-primary-bg)]'
                    : 'hover:bg-gray-50')
                }
              >
                {STYLE_LABEL[k]}
              </button>
            );
          })}
        </div>
      </div>

      <div className="mt-6 flex items-center justify-center gap-4">
        <button
          disabled={disabled}
          onClick={() => onGenerate()}
          className="inline-flex items-center gap-2 rounded-md bg-[var(--color-primary)] px-8 py-2 text-white disabled:opacity-50"
        >
          {loading ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />}
          이미지 생성하기
        </button>

        <Tooltip content="프롬프트에 템플릿 추가" side="bottom">
          <button
            onClick={() =>
              onReusePrompt(
                `${STYLE_LABEL[style]} 스타일, ${size} 해상도, 포근한 크리스마스 감성, 눈이 내리는 분위기, 따뜻한 조명`
              )
            }
            className="inline-flex items-center gap-2 rounded-md border px-4 py-2 hover:bg-gray-50"
            disabled={loading}
          >
            <Wand2 size={16} />
            스타일 템플릿
          </button>
        </Tooltip>
      </div>
    </div>
  );
}
