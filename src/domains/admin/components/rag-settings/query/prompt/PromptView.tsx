import type { Prompt } from '@/domains/admin/types/rag-settings/prompts.types';
import { Brain, User } from 'lucide-react';

type Props = {
  selected: Prompt | null;
  draft: Prompt | null;
};

export default function PromptView({ selected, draft }: Props) {
  const rawType = draft?.type ?? selected?.type;
  const type = rawType === 'system' ? 'SYSTEM' : 'USER';
  const isSystem = rawType === 'system';

  const systemColor = '#96257A';
  const userColor = '#135D9C';

  const bg = isSystem ? `${systemColor}20` : `${userColor}20`;
  const border = isSystem ? `${systemColor}40` : `${userColor}40`;
  const text = isSystem ? `${systemColor}` : `${userColor}`;

  return (
    <div className="mt-4 rounded-xl border bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="text-sm text-gray-500">프롬프트 이름</div>
          <div className="mt-0.5 text-base font-semibold text-gray-900">
            {selected?.name ?? '-'}
          </div>
        </div>

        <span
          className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold transition-all border shadow-sm"
          style={{
            backgroundColor: bg,
            borderColor: border,
            color: text,
          }}
        >
          {isSystem ? (
            <Brain size={12} className="opacity-90" />
          ) : (
            <User size={12} className="opacity-90" />
          )}
          {type}
        </span>
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
