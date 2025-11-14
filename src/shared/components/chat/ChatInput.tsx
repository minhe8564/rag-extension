import { useRef, useState, useEffect } from 'react';
import { SendHorizonal } from 'lucide-react';

type ChatMode = 'llm' | 'rag';

type Props = {
  onSend: (msg: string) => void;
  variant?: 'retina' | 'hebees';
  mode?: ChatMode;
  onChangeMode?: (mode: ChatMode) => void;
};

export default function ChatInput({
  onSend,
  variant = 'retina',
  mode = 'llm',
  onChangeMode,
}: Props) {
  const [text, setText] = useState('');
  const composingRef = useRef(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const [isTall, setIsTall] = useState(false);

  const send = () => {
    const content = text.trim();
    if (!content) return;
    onSend(content);
    setText('');
    requestAnimationFrame(() => {
      const el = textareaRef.current;
      if (!el) return;
      el.style.height = 'auto';
      el.style.height = `${el.scrollHeight}px`;
      setIsTall(el.scrollHeight > 60);
    });
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key !== 'Enter') return;

    const native = e.nativeEvent;
    if (native.isComposing || composingRef.current || native.keyCode === 229) {
      return;
    }

    if (e.shiftKey) return;

    e.preventDefault();
    send();
  };

  const onCompositionStart = () => {
    composingRef.current = true;
  };

  const onCompositionEnd = () => {
    composingRef.current = false;
  };

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;

    el.style.height = 'auto';
    el.style.height = `${el.scrollHeight}px`;

    setIsTall(el.scrollHeight > 60);
  }, [text]);

  const buttonColor =
    variant === 'hebees'
      ? 'bg-[var(--color-hebees)] hover:bg-[var(--color-hebees-dark)]'
      : 'bg-[var(--color-retina)] hover:bg-[var(--color-retina-dark)]';

  const isDisabled = text.trim().length === 0;

  const brandLabel = variant === 'hebees' ? '히비스 챗봇' : '레티나 챗봇';

  const handleChangeMode = (next: ChatMode) => {
    if (onChangeMode) onChangeMode(next);
  };

  const helperText =
    mode === 'rag'
      ? `${brandLabel}은(는) 업로드된 문서를 기반으로 답변합니다.`
      : `${brandLabel}은(는) 일반 LLM 대화 모드로 응답합니다.`;

  return (
    <div className="flex flex-col items-center w-full gap-3">
      <div className="w-full flex items-center justify-between px-1">
        <div className="inline-flex items-center gap-1 rounded-full bg-gray-100 p-1 text-sm">
          <button
            type="button"
            onClick={() => handleChangeMode('llm')}
            className={`px-4 py-1 rounded-full transition ${
              mode === 'llm'
                ? 'bg-white shadow-sm text-gray-900'
                : 'text-gray-500 hover:text-gray-800'
            }`}
          >
            일반 LLM
          </button>
          <button
            type="button"
            onClick={() => handleChangeMode('rag')}
            className={`px-3 py-1 rounded-full transition ${
              mode === 'rag'
                ? 'bg-white shadow-sm text-gray-900'
                : 'text-gray-500 hover:text-gray-800'
            }`}
          >
            RAG 모드
          </button>
        </div>
      </div>

      <div className="w-full bg-white pb-4">
        <div
          className={`
            border border-gray-300 px-3 py-2 transition-all
            ${isTall ? 'rounded-xl' : 'rounded-full'}
          `}
        >
          <div className="flex items-end gap-2">
            <textarea
              ref={textareaRef}
              className="flex-1 w-full text-base border-none text-black placeholder-gray-400
                 resize-none overflow-hidden leading-[1.3] min-h-[24px] max-h-[40vh]
                 focus:outline-none focus:ring-0"
              placeholder={`${brandLabel}에게 무엇이든 물어보세요.`}
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={onKeyDown}
              onCompositionStart={onCompositionStart}
              onCompositionEnd={onCompositionEnd}
              rows={1}
            />

            <button
              type="button"
              disabled={isDisabled}
              className={`shrink-0 self-end w-9 h-9 flex items-center justify-center rounded-full transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${buttonColor}`}
              onClick={send}
              aria-label="메시지 전송"
            >
              <SendHorizonal size={18} className="text-white" />
            </button>
          </div>
        </div>
        <p className="text-xs text-gray-500 mt-3 flex justify-center">{helperText}</p>
      </div>
    </div>
  );
}
