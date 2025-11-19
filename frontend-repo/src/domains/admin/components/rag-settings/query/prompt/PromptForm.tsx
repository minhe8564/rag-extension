import type { Prompt, PromptType } from '@/domains/admin/types/rag-settings/prompts.types';

type Props = {
  draft: Prompt | null;
  disabled?: boolean;
  makeDescription: (content: string, max?: number) => string;
  onChangeDraft: (updater: (prev: Prompt | null) => Prompt) => void;
  onDirty: () => void;
};

const DEFAULT_TYPE: PromptType = 'user';

export default function PromptForm({
  draft,
  disabled,
  makeDescription,
  onChangeDraft,
  onDirty,
}: Props) {
  const type = draft?.type ?? DEFAULT_TYPE;

  return (
    <div className="space-y-4 mt-4">
      <div className="space-y-1">
        <label className="text-sm font-medium text-gray-700">프롬프트 타입</label>

        <div className="flex gap-2 bg-gray-100 rounded-md p-1 w-fit">
          {(['user', 'system'] as PromptType[]).map((t) => {
            const active = t === type;
            return (
              <button
                key={t}
                type="button"
                disabled={disabled}
                onClick={() => {
                  if (!draft || type === t) return;
                  onChangeDraft(() => ({ ...(draft as Prompt), type: t }));
                  onDirty();
                }}
                className={[
                  'px-4 py-1.5 text-sm rounded-md font-medium transition-all',
                  active
                    ? 'bg-[var(--color-hebees)] text-white shadow-sm'
                    : 'text-gray-600 hover:text-gray-800 ',
                  disabled && 'opacity-60 cursor-not-allowed',
                ].join(' ')}
              >
                {t.toUpperCase()}
              </button>
            );
          })}
        </div>
      </div>

      <div className="space-y-1">
        <label className="text-sm font-medium text-gray-700">프롬프트 이름</label>
        <input
          className="
            w-full rounded-md border border-gray-200 bg-white px-3 py-2.5 text-sm 
            focus:border-[var(--color-hebees)] focus:bg-[var(--color-hebees-bg)]
            focus:ring-0 transition-all placeholder:text-gray-400
          "
          value={draft?.name ?? ''}
          onChange={(e) => {
            if (!draft) return;
            onChangeDraft(() => ({ ...(draft as Prompt), name: e.target.value }));
            onDirty();
          }}
          placeholder="예: 요약 시스템 프롬프트"
          disabled={disabled}
        />
      </div>

      <div className="space-y-1">
        <label className="text-sm font-medium text-gray-700">프롬프트 내용</label>
        <textarea
          className="
            w-full min-h-[300px] rounded-md border border-gray-200 bg-white px-3 py-3 text-sm leading-6
            focus:border-[var(--color-hebees)] focus:bg-[var(--color-hebees-bg)]
            focus:ring-0 transition-all placeholder:text-gray-400
          "
          value={draft?.content ?? ''}
          onChange={(e) => {
            if (!draft) return;
            const content = e.target.value;
            onChangeDraft(() => ({
              ...(draft as Prompt),
              content,
              description: makeDescription(content),
              type: draft?.type ?? DEFAULT_TYPE,
            }));
            onDirty();
          }}
          placeholder="프롬프트 지시문을 입력하세요 ({{variable}} 변수를 사용할 수 있어요)"
          disabled={disabled}
        />
      </div>
    </div>
  );
}
