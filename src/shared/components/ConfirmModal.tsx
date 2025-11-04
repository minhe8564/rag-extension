import { useEffect, useId } from 'react';

interface ConfirmModalProps {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title?: string;
  message?: string;
  confirmText?: string;
  cancelText?: string;
  variant?: 'primary' | 'danger';
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

  return (
    <div
      className="fixed inset-0 bg-black/70 flex justify-center items-center z-50"
      onClick={e => e.target === e.currentTarget && onClose()}
      role="dialog"
      aria-labelledby={id}
      aria-modal="true"
    >
      <div className="bg-white rounded-lg shadow-2xl p-8 w-full max-w-md">
        <h2 className="text-2xl font-bold text-center mb-6">{title}</h2>

        <p className="mb-6 text-center text-base text-gray-600 whitespace-pre-line">{message}</p>

        <div className="flex justify-center gap-3">
          <button
            onClick={onClose}
            className="rounded-md bg-gray-200 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-300"
          >
            {cancelText}
          </button>
          <button
            onClick={onConfirm}
            className={`rounded-md px-4 py-2 text-sm font-regular ${confirmColor}`}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}
