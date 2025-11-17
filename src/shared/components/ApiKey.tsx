import { useEffect, useMemo, useRef, useState } from 'react';
import { toast } from 'react-toastify';
import {
  getMyLlmKeyByName,
  createMyLlmKey,
  updateMyLlmKey,
  deleteMyLlmKey,
} from '@/shared/api/llm.api';
import type { MyLlmKeyResponse } from '@/shared/types/llm.types';
import { KeyRound, Eye, EyeOff, Check, X, Pencil, Trash2, Copy } from 'lucide-react';
import Tooltip from '@/shared/components/controls/Tooltip';
import ConfirmModal from '@/shared/components/ConfirmModal';

function IconButton({
  tooltip,
  onClick,
  disabled,
  children,
}: {
  tooltip: string;
  onClick?: () => void;
  disabled?: boolean;
  children: React.ReactNode;
}) {
  return (
    <Tooltip content={tooltip} side="bottom">
      <button
        type="button"
        onClick={onClick}
        disabled={disabled}
        className="
          inline-flex size-9 items-center justify-center rounded-md
          border border-gray-200 bg-white text-gray-700
          transition hover:bg-gray-50
          focus:outline-none focus-visible:ring-2 focus-visible:ring-black/10
          disabled:cursor-not-allowed disabled:opacity-60
        "
      >
        {children}
      </button>
    </Tooltip>
  );
}

type ApiKeyProps = {
  label?: string;
  brand?: 'hebees' | 'retina';
  className?: string;
};

const NAME_TO_ID: Record<string, string> = {
  'GPT-4o': 'gpt-4o',
  'Gemini 2.5 Flash': 'gemini 2.5 flash',
  'Claude Sonnet 4': 'claude sonnet 4',
};
const NAMES = Object.keys(NAME_TO_ID);

export default function ApiKey({
  label = 'LLM API Key',
  brand = 'retina',
  className = '',
}: ApiKeyProps) {
  const [selectedName, setSelectedName] = useState(NAMES[1] || NAMES[0]);
  const [current, setCurrent] = useState<MyLlmKeyResponse | null>(null);
  const [tempKey, setTempKey] = useState('');
  const [editingKey, setEditingKey] = useState(false);
  const [showKey, setShowKey] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [confirmOpen, setConfirmOpen] = useState(false);

  const abortRef = useRef<AbortController | null>(null);

  const brandColor = brand === 'hebees' ? 'var(--color-hebees)' : 'var(--color-retina)';
  const brandBg = brand === 'hebees' ? 'var(--color-hebees-bg)' : 'var(--color-retina-bg)';

  const maskedKey = useMemo(() => {
    const k = current?.apiKey || '';
    if (!k) return '-';
    if (showKey) return k;
    return `${k.slice(0, 4)}••••••••••••${k.slice(-4)}`;
  }, [current, showKey]);

  useEffect(() => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    const load = async () => {
      setIsLoading(true);
      try {
        const llmName = NAME_TO_ID[selectedName].toLowerCase();
        const res = await getMyLlmKeyByName(llmName);
        if (controller.signal.aborted) return;
        const record = res.data.result as MyLlmKeyResponse | null;

        if (!record || !record.hasKey) {
          setCurrent(null);
          setTempKey('');
        } else {
          setCurrent(record);
          setTempKey(record.apiKey ?? '');
        }
      } finally {
        if (!controller.signal.aborted) setIsLoading(false);
      }
    };

    load();
    return () => controller.abort();
  }, [selectedName]);

  const onSave = async () => {
    const value = tempKey.trim();
    if (!value) {
      toast.warn('키를 입력해주세요.');
      return;
    }
    setIsSaving(true);
    try {
      if (current) {
        const res = await updateMyLlmKey(current.llmNo, { apiKey: value });
        setCurrent(res.data.result);
        toast.success('API Key 수정 완료');
      } else {
        const res = await createMyLlmKey({
          llm: NAME_TO_ID[selectedName].toLowerCase(),
          apiKey: value,
        });
        setCurrent(res.data.result);
        toast.success('API Key 등록 완료');
      }
      setEditingKey(false);
    } finally {
      setIsSaving(false);
    }
  };

  const onDelete = () => {
    if (!current) return;
    setConfirmOpen(true);
  };

  const confirmDelete = async () => {
    if (!current) {
      setConfirmOpen(false);
      return;
    }
    setIsSaving(true);
    try {
      await deleteMyLlmKey(current.llmNo);
      setCurrent(null);
      setTempKey('');
      setEditingKey(false);
      toast.success('API Key 삭제 완료');
    } finally {
      setIsSaving(false);
      setConfirmOpen(false);
    }
  };

  const copyKey = async () => {
    if (!current?.apiKey) return;
    await navigator.clipboard.writeText(current.apiKey);
    toast.success('API Key가 복사되었습니다');
  };

  return (
    <>
      <section
        className={`relative flex items-start gap-5 rounded-xl border border-gray-200 bg-white p-4 ${className}`}
      >
        <div
          className="p-2.5 rounded-md flex items-center justify-center shrink-0"
          style={{ backgroundColor: brandBg, color: brandColor }}
        >
          <KeyRound size={22} strokeWidth={1.8} />
        </div>

        <div className="flex-1 min-w-0">
          <div className="mb-2 flex items-center justify-between">
            <div className="text-[13px] text-gray-500">{label}</div>

            <div className="flex gap-1 rounded-md bg-gray-100 p-1">
              {NAMES.map((n) => (
                <button
                  key={n}
                  type="button"
                  onClick={() => {
                    setSelectedName(n);
                    setEditingKey(false);
                    setShowKey(false);
                  }}
                  className={`px-3 py-1.5 text-xs rounded-lg transition ${
                    selectedName === n
                      ? 'bg-white shadow text-gray-900'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  {n}
                </button>
              ))}
            </div>
          </div>

          {!editingKey ? (
            <div className="flex items-center justify-between">
              <div
                className="
                  text-base font-semibold text-gray-900 tabular-nums min-h-[28px]
                  min-w-[160px] truncate
                "
              >
                {isLoading ? (
                  <span className="text-gray-400">-</span>
                ) : current ? (
                  maskedKey
                ) : (
                  <span className="text-gray-400">-</span>
                )}
              </div>

              <div className="flex gap-1.5">
                {current && (
                  <>
                    <IconButton
                      tooltip={showKey ? '숨기기' : '보기'}
                      onClick={() => setShowKey(!showKey)}
                      disabled={isSaving || isLoading}
                    >
                      {showKey ? <EyeOff size={16} /> : <Eye size={16} />}
                    </IconButton>

                    <IconButton tooltip="복사" onClick={copyKey} disabled={isSaving || isLoading}>
                      <Copy size={16} />
                    </IconButton>

                    <IconButton tooltip="삭제" onClick={onDelete} disabled={isSaving || isLoading}>
                      <Trash2 size={16} />
                    </IconButton>
                  </>
                )}

                <IconButton
                  tooltip={current ? '수정' : '등록'}
                  onClick={() => {
                    setEditingKey(true);
                    setTempKey(current?.apiKey ?? '');
                    setShowKey(false);
                  }}
                  disabled={isLoading}
                >
                  <Pencil size={16} />
                </IconButton>
              </div>
            </div>
          ) : (
            <div className="mt-3 flex items-center gap-2">
              <div className="flex-1 flex items-center gap-2">
                <input
                  type={showKey ? 'text' : 'password'}
                  className="
                    flex-1 rounded-md border border-gray-200 bg-white
                    px-3 py-2 text-sm outline-none
                    focus:border-gray-400 focus-visible:ring-0
                    transition
                  "
                  placeholder="API Key 입력"
                  value={tempKey}
                  onChange={(e) => setTempKey(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') onSave();
                    if (e.key === 'Escape') {
                      setEditingKey(false);
                      setTempKey(current?.apiKey ?? '');
                    }
                  }}
                  autoFocus
                />

                <IconButton
                  tooltip={showKey ? '숨기기' : '보기'}
                  onClick={() => setShowKey(!showKey)}
                  disabled={isSaving}
                >
                  {showKey ? <EyeOff size={16} /> : <Eye size={16} />}
                </IconButton>
              </div>

              <IconButton tooltip="저장" onClick={onSave} disabled={!tempKey.trim() || isSaving}>
                <Check size={16} />
              </IconButton>

              <IconButton
                tooltip="취소"
                onClick={() => {
                  setEditingKey(false);
                  setTempKey(current?.apiKey ?? '');
                }}
                disabled={isSaving}
              >
                <X size={16} />
              </IconButton>
            </div>
          )}
        </div>
      </section>

      <ConfirmModal
        open={confirmOpen}
        onClose={() => setConfirmOpen(false)}
        onConfirm={confirmDelete}
        title={`${selectedName} 키 삭제`}
        message={`정말로 삭제할까요?\n삭제 후 되돌릴 수 없습니다.`}
        confirmText={isSaving ? '삭제 중…' : '삭제'}
        cancelText="취소"
        variant="danger"
        zIndex={10050}
      />
    </>
  );
}
