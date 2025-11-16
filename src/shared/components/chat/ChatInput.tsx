import { useRef, useState, useEffect } from 'react';
import { ArrowDown, ArrowUp, Square } from 'lucide-react';
import clsx from 'clsx';

type ChatMode = 'llm' | 'rag';

type Props = {
  onSend: (msg: string) => void;
  variant?: 'retina' | 'hebees';
  mode?: ChatMode;
  onChangeMode?: (mode: ChatMode) => void;
  watch?: number;
  disabled?: boolean;
  loading?: boolean;
  onStop?: () => void;
};

export default function ChatInput({
  onSend,
  variant = 'retina',
  mode = 'llm',
  onChangeMode,
  watch,
  disabled = false,
  loading = false,
  onStop,
}: Props) {
  const [text, setText] = useState('');
  const composingRef = useRef(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const [isTall, setIsTall] = useState(false);
  const [showScrollButton, setShowScrollButton] = useState(false);
  const [hasUnseen, setHasUnseen] = useState(false);

  const trimmed = text.trim();

  const canSend = !disabled && !loading && trimmed.length > 0;
  const isStopMode = !!onStop && loading;
  const isButtonDisabled = disabled || (!isStopMode && !canSend);

  const send = () => {
    if (!canSend) return;
    onSend(trimmed);
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
    if (disabled || loading) return;

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

    setIsTall(el.scrollHeight > 40);
  }, [text]);

  const isAtBottom = () => {
    const doc = document.documentElement;
    const scrollTop = window.scrollY || doc.scrollTop;
    const clientHeight = window.innerHeight;
    const scrollHeight = doc.scrollHeight;

    const delta = scrollHeight - (scrollTop + clientHeight);
    return delta <= 300;
  };

  const scrollToBottom = () => {
    const doc = document.documentElement;
    const scrollHeight = doc.scrollHeight;
    window.scrollTo({
      top: scrollHeight,
      behavior: 'smooth',
    });
  };

  useEffect(() => {
    const handleScroll = () => {
      const atBottom = isAtBottom();
      setShowScrollButton(!atBottom);
      if (atBottom) {
        setHasUnseen(false);
      }
    };

    // handleScroll();
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  useEffect(() => {
    if (watch === undefined) return;
    if (!isAtBottom()) {
      setHasUnseen(true);
    }
  }, [watch]);

  const buttonColor =
    variant === 'hebees'
      ? 'bg-[var(--color-hebees)] hover:bg-[var(--color-hebees-dark)]'
      : 'bg-[var(--color-retina)] hover:bg-[var(--color-retina-dark)]';

  const brandLabel = variant === 'hebees' ? '히비스 챗봇' : '레티나 챗봇';

  const helperText =
    mode === 'rag'
      ? `${brandLabel}은(는) 업로드된 문서를 기반으로 답변합니다.`
      : `${brandLabel}은(는) 일반 LLM 대화 모드로 응답합니다.`;

  return (
    <div className="relative flex flex-col items-center w-full gap-3">
      {showScrollButton && (
        <button
          type="button"
          onClick={() => {
            scrollToBottom();
            setHasUnseen(false);
          }}
          className={clsx(
            'absolute right-100 -top-1',
            'inline-flex items-center gap-2 rounded-full border bg-white px-3 py-2 text-sm shadow-lg',
            'text-gray-700 hover:bg-gray-50 transition',
            'focus:outline-none focus-visible:outline-none'
          )}
        >
          {hasUnseen && (
            <span className="relative mr-1 inline-flex h-2.5 w-2.5 items-center justify-center">
              <span className="absolute inline-flex h-full w-full rounded-full bg-red-500 opacity-60 animate-ping" />
              <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-red-500 animate-pulse" />
            </span>
          )}
          <ArrowDown size={16} />
          최신 메시지
        </button>
      )}

      <div className="w-full flex items-center justify-between px-1">
        <div className="inline-flex items-center gap-1 rounded-full bg-gray-100 p-1 text-sm">
          <button
            type="button"
            onClick={() => onChangeMode?.('llm')}
            className={`px-4 py-1 rounded-full transition ${
              mode === 'llm'
                ? 'bg-white shadow-sm text-gray-900'
                : 'text-gray-500 hover:text-gray-800'
            }`}
            disabled={disabled || loading}
          >
            일반 LLM
          </button>
          <button
            type="button"
            onClick={() => onChangeMode?.('rag')}
            className={`px-3 py-1 rounded-full transition ${
              mode === 'rag'
                ? 'bg-white shadow-sm text-gray-900'
                : 'text-gray-500 hover:text-gray-800'
            }`}
            disabled={disabled || loading}
          >
            RAG 모드
          </button>
        </div>
      </div>

      <div className="w-full bg-white pb-4">
        <div
          className={clsx(
            'border border-gray-300 px-3 py-2 transition-all',
            isTall ? 'rounded-xl' : 'rounded-full',
            disabled && 'bg-gray-50'
          )}
        >
          <div className="flex items-end gap-2">
            <textarea
              ref={textareaRef}
              className="flex-1 w-full text-base border-none text-black placeholder-gray-400
                 resize-none overflow-hidden leading-[1.3] min-h-[24px] max-h-[40vh]
                 focus:outline-none focus:ring-0 bg-transparent"
              placeholder={
                loading
                  ? '응답 생성 중입니다. 추가로 적어두고 싶은 내용이 있으면 입력해주세요.'
                  : `${brandLabel}에게 무엇이든 물어보세요.`
              }
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={onKeyDown}
              onCompositionStart={onCompositionStart}
              onCompositionEnd={onCompositionEnd}
              rows={1}
              disabled={disabled}
            />

            <button
              type="button"
              disabled={isButtonDisabled}
              className={clsx(
                'shrink-0 self-end w-9 h-9 flex items-center justify-center rounded-full transition-colors',
                'disabled:opacity-50 disabled:cursor-not-allowed',
                buttonColor
              )}
              onClick={() => {
                if (isStopMode) {
                  onStop?.();
                } else {
                  send();
                }
              }}
              aria-label={isStopMode ? '응답 중지' : '메시지 전송'}
            >
              {isStopMode ? (
                <Square size={16} strokeWidth={3} className="text-white" />
              ) : (
                <ArrowUp size={20} strokeWidth={2} className="text-white" />
              )}
            </button>
          </div>
        </div>

        <p className="text-xs text-gray-500 mt-3 flex justify-center">{helperText}</p>
      </div>
    </div>
  );
}
