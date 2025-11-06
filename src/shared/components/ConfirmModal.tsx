// ConfirmModal.tsx
import { useEffect, useId } from 'react';
import { createPortal } from 'react-dom';

interface ConfirmModalProps {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title?: string;
  message?: string;
  confirmText?: string;
  cancelText?: string;
  variant?: 'primary' | 'danger';
  zIndex?: number;
}

export default function ConfirmModal({
  open,
  onClose,
  onConfirm,
  title = '확인',
  message = '이 작업을 진행할까요?',
  confirmText = '확인',
  cancelText = '취소',
  variant = 'primary',
  zIndex = 10050,
}: ConfirmModalProps) {
  const id = useId();

  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => e.key === 'Escape' && onClose();
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [open, onClose]);

  if (!open) return null;

  const confirmColor =
    variant === 'danger'
      ? 'bg-black text-white hover:opacity-80'
      : 'bg-[var(--color-hebees-bg)] text-white hover:brightness-95';

  const node = (
    <div
      className="fixed inset-0 flex items-center justify-center"
      style={{ zIndex }}
      onClick={(e) => e.target === e.currentTarget && onClose()}
      role="dialog"
      aria-labelledby={id}
      aria-modal="true"
    >
      <div className="absolute inset-0 bg-black/70" />
      <div className="relative bg-white rounded-lg shadow-2xl p-8 w-full max-w-md">
        <h2 id={id} className="text-2xl font-bold text-center mb-6">
          {title}
        </h2>
        <p className="mb-6 text-center text-base text-gray-600 whitespace-pre-line">{message}</p>
        <div className="flex justify-center gap-3">
          <button
            onClick={onClose}
            className="rounded-md bg-gray-200 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-300"
          >
            {cancelText}
          </button>
          <button onClick={onConfirm} className={`rounded-md px-4 py-2 text-sm ${confirmColor}`}>
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );

  return createPortal(node, document.body);
}
