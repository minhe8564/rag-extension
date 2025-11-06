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
      ) : (
        <ChatMarkdown>{msg.content}</ChatMarkdown>
      )}

      {!isUser && msg.createdAt && (
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

      {!isUser && msg.messageNo && currentSessionNo ? (
        <ReferencedDocsPanel
          sessionNo={currentSessionNo}
          messageNo={msg.messageNo}
          collapsedByDefault={false}
        />
      ) : null}
    </div>
  );
}
