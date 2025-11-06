import { useRef, useState } from 'react';
import { SendHorizonal } from 'lucide-react';

type Props = {
  onSend: (msg: string) => void;
  variant?: 'retina' | 'hebees';
};

export default function ChatInput({ onSend, variant = 'retina' }: Props) {
  const [text, setText] = useState('');
  const composingRef = useRef(false);

  const send = () => {
    const content = text.trim();
    if (!content) return;
    onSend(content);
    setText('');
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key !== 'Enter') return;

    const native = e.nativeEvent;
    if (
      (native as unknown as { isComposing?: boolean }).isComposing ||
      composingRef.current ||
      (typeof (native as KeyboardEvent).keyCode === 'number' &&
        (native as KeyboardEvent).keyCode === 229)
    ) {
      return;
    }

    e.preventDefault();
    send();
  };

  const onCompositionStart = () => {
    composingRef.current = true;
  };

  const onCompositionEnd = () => {
    composingRef.current = false;
  };

  const buttonColor =
    variant === 'hebees'
      ? 'bg-[var(--color-hebees)] hover:bg-[var(--color-hebees-dark)]'
      : 'bg-[var(--color-retina)] hover:bg-[var(--color-retina-dark)]';

  const isDisabled = text.trim().length === 0;

  return (
    <div className="flex flex-col items-center w-full gap-4">
      <div className="w-full">
        <div className="flex items-center rounded-full border border-gray-300 bg-white px-4 py-2 shadow-sm">
          <input
            className="flex-1 text-base bg-transparent border-none text-black placeholder-gray-400 
               focus:outline-none focus:ring-0"
            placeholder="레티나 챗봇에게 무엇이든 물어보세요."
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={onKeyDown}
            onCompositionStart={onCompositionStart}
            onCompositionEnd={onCompositionEnd}
          />
          <button
            type="button"
            aria-label="메시지 전송"
            disabled={isDisabled}
            className={`w-9 h-9 flex items-center justify-center rounded-full transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${buttonColor}`}
            onClick={send}
          >
            <SendHorizonal size={18} className="text-white" />
          </button>
        </div>
      </div>

      <p className="text-sm text-gray-500">레티나 챗봇은 업로드된 문서를 기반으로 답변합니다.</p>
    </div>
  );
}
