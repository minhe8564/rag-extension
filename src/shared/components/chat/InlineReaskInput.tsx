import { useEffect, useRef, useState } from 'react';
import { Check, X } from 'lucide-react';
import Tooltip from '@/shared/components/Tooltip';

type Props = {
  initialValue: string;
  onSubmit: (value: string) => void;
  onCancel: () => void;
  placeholder?: string;
  autoFocus?: boolean;
};

export default function InlineReaskInput({
  initialValue,
  onSubmit,
  onCancel,
  placeholder = '질문을 수정하세요…',
  autoFocus = true,
}: Props) {
  const [value, setValue] = useState(initialValue);
  const ref = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    if (autoFocus) {
      // textarea 높이 자동
      requestAnimationFrame(() => {
        if (ref.current) {
          ref.current.focus();
          ref.current.selectionStart = ref.current.value.length;
          ref.current.style.height = '0px';
          ref.current.style.height = ref.current.scrollHeight + 'px';
        }
      });
    }
  }, [autoFocus]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      const v = value.trim();
      if (v) onSubmit(v);
      return;
    }
    if (e.key === 'Escape') {
      e.preventDefault();
      onCancel();
    }
  };

  const syncHeight = () => {
    if (ref.current) {
      ref.current.style.height = '0px';
      ref.current.style.height = ref.current.scrollHeight + 'px';
    }
  };

  return (
    <div className="w-full">
      <textarea
        ref={ref}
        value={value}
        onChange={(e) => {
          setValue(e.target.value);
          syncHeight();
        }}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        rows={1}
        className="w-full resize-none rounded-md border px-2.5 py-1.5 text-sm outline-none focus:border-gray-400"
      />
      <div className="mt-2 flex items-center justify-end gap-2">
        <Tooltip content="취소" side="bottom">
          <button onClick={onCancel} className="rounded-md p-1.5 text-gray-600 hover:bg-gray-100">
            <X size={16} />
          </button>
        </Tooltip>
        <Tooltip content="보내기 (Enter)" side="bottom">
          <button
            onClick={() => {
              const v = value.trim();
              if (v) onSubmit(v);
            }}
            className="rounded-md p-1.5 text-[var(--color-retina)] hover:bg-gray-100"
          >
            <Check size={16} />
          </button>
        </Tooltip>
      </div>
    </div>
  );
}
