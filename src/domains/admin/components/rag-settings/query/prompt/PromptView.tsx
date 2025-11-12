import type { Prompt } from '@/domains/admin/types/rag-settings/prompts.types';

type Props = {
  selected: Prompt | null;
  draft: Prompt | null;
};

export default function PromptView({ selected, draft }: Props) {
  const type = (draft?.type ?? selected?.type) === 'system' ? 'SYSTEM' : 'USER';

  return (
    <div className="mt-4 rounded-xl border bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="text-sm text-gray-500">프롬프트 이름</div>
          <div className="mt-0.5 text-base font-semibold text-gray-900">
            {selected?.name ?? '-'}
          </div>
        </div>
        <span className="rounded-md bg-gray-100 px-2 py-1 text-xs text-gray-600">{type}</span>
      </div>

      <div className="mt-4">
        <div className="text-sm text-gray-500">프롬프트 내용</div>
        <pre className="mt-1 whitespace-pre-wrap rounded-xl border border-gray-100 bg-gray-50 p-3 text-sm text-gray-800 font-sans">
          {selected?.content || '내용이 없습니다.'}
        </pre>
      </div>
    </div>
  );
}
