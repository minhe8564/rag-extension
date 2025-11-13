import { Wand2 } from 'lucide-react';
import Tooltip from '@/shared/components/Tooltip';
import ChatMarkdown from '@/shared/components/chat/ChatMarkdown';
import InlineReaskInput from '@/shared/components/chat/InlineReaskInput';
import ReferencedDocsPanel from '@/shared/components/chat/ReferencedDocs';
import { formatCreatedAt } from '@/shared/utils/date';
import type { ReferencedDocument } from '@/shared/types/chat.types';

type Brand = 'retina' | 'hebees';
export type UiRole = 'user' | 'assistant' | 'system' | 'tool';

export type UiMsg = {
  role: UiRole;
  content: string;
  createdAt?: string;
  messageNo?: string;
  referencedDocuments?: ReferencedDocument[];
};

type Props = {
  msg: UiMsg;
  index: number;
  currentSessionNo: string | null;
  isEditing: boolean;
  editingDraft: string;
  onStartReask: (idx: number, content: string) => void;
  onCancelReask: () => void;
  onSubmitReask: (value: string) => void;
  isPendingAssistant?: boolean;
  pendingSubtitle: string;
  brand: Brand;
};

const brandBgClass: Record<Brand, string> = {
  retina: 'bg-[var(--color-retina-bg)]',
  hebees: 'bg-[var(--color-hebees-bg)]',
};

export default function ChatMessageItem({
  msg,
  index,
  currentSessionNo,
  isEditing,
  editingDraft,
  onStartReask,
  onCancelReask,
  onSubmitReask,
  isPendingAssistant = false,
  pendingSubtitle,
  brand = 'retina',
}: Props) {
  const isUser = msg.role === 'user';
  const userBubbleBase = `rounded-xl border ml-auto ${brandBgClass[brand]} text-black border-gray-200`;

  return (
    <div
      className={`
        relative group break-words overflow-visible
        ${isUser ? (isEditing ? 'w-full max-w-lg' : 'w-fit max-w-[60%]') : 'w-full'}
        ${isUser ? userBubbleBase : 'bg-white'}
        px-3 py-1.5
      `}
    >
      {isEditing && isUser ? (
        <InlineReaskInput
          initialValue={editingDraft || msg.content}
          onCancel={onCancelReask}
          onSubmit={onSubmitReask}
        />
      ) : !isUser && isPendingAssistant ? (
        <div className="flex items-center gap-3 py-1.5">
          <span className="relative inline-flex h-6 w-6">
            <span
              className="
                absolute inset-0 rounded-full opacity-90
                bg-[linear-gradient(90deg,#BE7DB1_0%,#81BAFF_100%)]
                animate-[spin_1.1s_linear_infinite]
              "
            />
            <span
              className="
                absolute inset-0 rounded-full
                bg-gradient-to-br from-white/40 to-transparent
                mix-blend-overlay
              "
            />
          </span>

          <span
            className="
              text-sm font-medium bg-clip-text text-transparent
              bg-[linear-gradient(90deg,#BE7DB1_0%,#81BAFF_50%,#BE7DB1_100%)]
              bg-[length:200%_200%] animate-gradientMove
              whitespace-nowrap
            "
          >
            {pendingSubtitle}
          </span>
        </div>
      ) : (
        <ChatMarkdown>{msg.content}</ChatMarkdown>
      )}

      {!isUser && msg.createdAt && !isPendingAssistant && (
        <div className="mt-1 text-xs text-gray-400">{formatCreatedAt(msg.createdAt)}</div>
      )}

      <div
        className={`
          absolute z-20 flex items-center gap-2
          ${isUser ? 'right-2' : 'left-2'}
          top-full mt-1
          opacity-0 transition-opacity duration-200
          group-hover:opacity-100 hover:opacity-100
          pointer-events-none
        `}
      >
        {isUser && !isEditing && (
          <Tooltip content="질문 재생성 (수정 후 전송)" side="bottom">
            <button
              onClick={() => onStartReask(index, msg.content)}
              className="p-1 rounded hover:bg-gray-100 pointer-events-auto"
            >
              <Wand2 size={14} className="text-gray-500" />
            </button>
          </Tooltip>
        )}
      </div>

      {!isUser && msg.messageNo && currentSessionNo && !isPendingAssistant ? (
        <ReferencedDocsPanel
          sessionNo={currentSessionNo}
          messageNo={msg.messageNo}
          collapsedByDefault={false}
        />
      ) : null}
    </div>
  );
}
