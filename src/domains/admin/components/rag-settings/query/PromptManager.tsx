import { useMemo, useState } from 'react';
import { Plus, Save, Trash2 } from 'lucide-react';
import Select from '@/shared/components/Select';
import ConfirmModal from '@/shared/components/ConfirmModal';

type Prompt = { id: string; name: string; content: string };

type Props = {
  storageKey: string;
  initialPrompts?: Prompt[];
  onChange?: (prompts: Prompt[]) => void;
};

const uid = () => Math.random().toString(36).slice(2, 10);

export default function PromptManager({ storageKey, initialPrompts, onChange }: Props) {
  const lsKey = `pm:${storageKey}`;

  const load = (): Prompt[] => {
    const raw = localStorage.getItem(lsKey);
    if (raw) return JSON.parse(raw);
    return initialPrompts ?? [];
  };

  const [prompts, setPrompts] = useState<Prompt[]>(load());
  const [selectedId, setSelectedId] = useState<string | null>(prompts[0]?.id ?? null);
  const [draft, setDraft] = useState<Prompt | null>(prompts[0] ?? null);
  const [isNew, setIsNew] = useState(false);
  const [isDirty, setIsDirty] = useState(false);
  const [openDelete, setOpenDelete] = useState(false);

  const selected = useMemo(
    () => (selectedId ? (prompts.find((p) => p.id === selectedId) ?? null) : null),
    [prompts, selectedId]
  );

  const selectOptions = useMemo(
    () =>
      prompts.map((p) => ({
        label: p.name,
        value: p.id,
        desc: p.content.slice(0, 60),
      })),
    [prompts]
  );

  const persist = (next: Prompt[]) => {
    setPrompts(next);
    localStorage.setItem(lsKey, JSON.stringify(next));
    onChange?.(next);
  };

  const handleSelect = (id: string) => {
    const target = prompts.find((p) => p.id === id);
    if (!target) return;
    setSelectedId(id);
    setDraft({ ...target });
    setIsNew(false);
    setIsDirty(false);
  };

  const addNew = () => {
    const fresh: Prompt = { id: uid(), name: '', content: '' };
    setDraft(fresh);
    setSelectedId(null);
    setIsNew(true);
    setIsDirty(true);
  };

  const onClickDelete = () => {
    if (isNew || !selected) return;
    setOpenDelete(true);
  };

  const confirmDelete = () => {
    if (!selected) return;

    const next = prompts.filter((p) => p.id !== selected.id);
    persist(next);

    if (next.length === 0) {
      setSelectedId(null);
      setDraft(null);
    } else {
      setSelectedId(next[0].id);
      setDraft({ ...next[0] });
    }
    setIsNew(false);
    setIsDirty(false);
    setOpenDelete(false);
  };

  const save = () => {
    if (!(draft && (isDirty || isNew))) return;

    if (isNew) {
      const next = [draft, ...prompts];
      persist(next);
      setSelectedId(draft.id);
      setIsNew(false);
      setIsDirty(false);
      return;
    }

    if (!selected) return;
    const next = prompts.map((p) => (p.id === selected.id ? { ...draft } : p));
    persist(next);
    setIsDirty(false);
  };

  return (
    <>
      <div className="space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          <div className="max-w-xs w-full">
            <Select
              value={isNew ? null : selectedId}
              onChange={(id) => handleSelect(id)}
              options={selectOptions}
              placeholder="템플릿 선택"
              disabled={prompts.length === 0}
              className="focus:outline-none"
            />
          </div>

          <button
            type="button"
            onClick={addNew}
            className="inline-flex items-center gap-2 rounded-lg border bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60"
            title="새 템플릿"
          >
            <Plus className="size-4" /> 새 템플릿
          </button>

          <button
            type="button"
            onClick={onClickDelete}
            disabled={isNew || !selected}
            className={`flex items-center gap-2 rounded-lg text-gray-700 border border-gray-200 px-3 py-2 text-sm font-medium ${
              isNew || !selected
                ? 'cursor-not-allowed opacity-40'
                : 'border-black text-black hover:bg-gray-50'
            }`}
            title={
              isNew
                ? '새 템플릿은 삭제할 항목이 없어요'
                : !selected
                  ? '선택된 템플릿이 없어요'
                  : '삭제'
            }
          >
            <Trash2 className="size-4" /> 삭제
          </button>

          <button
            type="button"
            onClick={save}
            disabled={!(draft && (isDirty || isNew))}
            className={`flex items-center gap-2 rounded-lg text-gray-700 border border-gray-200 px-3 py-2 text-sm font-medium ${
              draft && (isDirty || isNew)
                ? 'border-[var(--color-hebees)] text-[var(--color-hebees)] hover:bg-[var(--color-hebees-bg)]'
                : 'cursor-not-allowed opacity-40'
            }`}
            title={draft && (isDirty || isNew) ? '저장' : '변경 사항이 없어요'}
          >
            <Save className="size-4" /> 저장
          </button>
        </div>

        <input
          className="w-full rounded-md border border-gray-200 px-3 py-2 text-base focus:outline-none focus:ring-0 focus:border-gray-400"
          value={draft?.name ?? ''}
          onChange={(e) => {
            if (!draft) return;
            setDraft((d) => ({ ...(d as Prompt), name: e.target.value }));
            setIsDirty(true);
          }}
          placeholder="프롬프트 이름"
          disabled={!draft}
        />

        <textarea
          className="w-full min-h-[240px] rounded-md border border-gray-200 px-3 py-2 text-sm leading-6 focus:outline-none focus:ring-0 focus:border-gray-400"
          value={draft?.content ?? ''}
          onChange={(e) => {
            if (!draft) return;
            setDraft((d) => ({ ...(d as Prompt), content: e.target.value }));
            setIsDirty(true);
          }}
          placeholder="프롬프트 내용을 입력하세요"
          disabled={!draft}
        />
      </div>
      <ConfirmModal
        open={openDelete}
        onClose={() => setOpenDelete(false)}
        onConfirm={confirmDelete}
        title="템플릿을 삭제할까요?"
        message={`"${selected?.name ?? ''}" 템플릿을 \n 삭제하면 되돌릴 수 없습니다.`}
        confirmText="삭제"
        cancelText="취소"
        variant="danger"
      />
    </>
  );
}
