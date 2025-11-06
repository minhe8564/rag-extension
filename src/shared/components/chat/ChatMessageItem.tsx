import { Wand2 } from 'lucide-react';
import Tooltip from '@/shared/components/Tooltip';
import ChatMarkdown from '@/shared/components/chat/ChatMarkdown';
import InlineReaskInput from '@/shared/components/chat/InlineReaskInput';
import ReferencedDocsPanel from '@/shared/components/chat/ReferencedDocs';
import { formatIsoDatetime } from '@/shared/util/iso';
import type { ReferencedDocument } from '@/shared/types/chat.types';

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
}: Props) {
  const isUser = msg.role === 'user';

  return (
    <div
      className={`
        px-3 py-1.5 relative group break-words
        ${isUser ? (isEditing ? 'w-full max-w-lg' : 'w-fit max-w-[60%]') : 'w-full'}
        ${isUser ? 'rounded-xl border ml-auto bg-[var(--color-retina-bg)] text-black' : 'bg-white'}
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
          {/* 회전하는 그라데이션 원 (꽉 찬 원) */}
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
        <div className="text-xs text-gray-400 mt-1">{formatIsoDatetime(msg.createdAt)}</div>
      )}

      <div
        className={`
          absolute flex gap-2 items-center
          ${isUser ? 'right-2' : 'left-2'}
          bottom-[-30px] opacity-0 group-hover:opacity-100
          transition-opacity duration-200
        `}
      >
        {isUser && !isEditing && (
          <Tooltip content="질문 재생성 (수정 후 전송)" side="bottom">
            <button
              onClick={() => onStartReask(index, msg.content)}
              className="p-1 rounded hover:bg-gray-100"
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
