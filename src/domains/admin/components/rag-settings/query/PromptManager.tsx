import { useEffect, useMemo, useState } from 'react';
import { Plus, Save, Trash2 } from 'lucide-react';
import Select from '@/shared/components/Select';
import ConfirmModal from '@/shared/components/ConfirmModal';
import { toast } from 'react-toastify';

import type { PromptType, Prompt } from '@/domains/admin/types/rag-settings/prompts.types';
import {
  getPrompts,
  getPromptDetail,
  createPrompt,
  updatePrompt,
  deletePrompt,
} from '@/domains/admin/api/rag-settings/prompts.api';

type Props = {
  storageKey: string;
  initialPrompts?: Array<{ id: string; name: string; content: string }>;
  onChange?: (prompts: Prompt[]) => void;
};

const DEFAULT_TYPE: PromptType = 'user';
const makeDescription = (content: string, max = 120) =>
  (content ?? '').replace(/\s+/g, ' ').slice(0, max);

export default function PromptManager({ initialPrompts, onChange }: Props) {
  const [prompts, setPrompts] = useState<Prompt[]>(
    (initialPrompts ?? []).map((p) => ({
      promptNo: p.id,
      name: p.name,
      content: p.content,
      type: DEFAULT_TYPE,
      description: makeDescription(p.content),
    }))
  );

  const [selectedNo, setSelectedNo] = useState<string | null>(prompts[0]?.promptNo ?? null);
  const [draft, setDraft] = useState<Prompt | null>(prompts[0] ?? null);

  const [isNew, setIsNew] = useState(false);
  const [isDirty, setIsDirty] = useState(false);

  const [openDelete, setOpenDelete] = useState(false);

  const [listLoading, setListLoading] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false); // ✅ 복구됨

  const reloadList = async (selectAfter?: string | null) => {
    setListLoading(true);

    const { data } = await getPrompts({ pageNum: 1, pageSize: 100 });

    setPrompts(data);
    onChange?.(data);

    const nextId = selectAfter ?? data[0]?.promptNo ?? null;
    setSelectedNo(nextId);

    if (nextId) {
      const detail = await getPromptDetail(nextId);
      setDraft(detail);
    } else {
      setDraft(null);
    }

    setIsNew(false);
    setIsDirty(false);
    setListLoading(false);
  };

  useEffect(() => {
    reloadList(selectedNo);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const selected = useMemo(
    () => (selectedNo ? (prompts.find((p) => p.promptNo === selectedNo) ?? null) : null),
    [prompts, selectedNo]
  );

  const selectOptions = useMemo(
    () =>
      prompts.map((p) => ({
        label: p.name,
        value: p.promptNo,
        desc: p.description || makeDescription(p.content ?? ''),
      })),
    [prompts]
  );

  const handleSelect = async (id: string) => {
    setDetailLoading(true);

    const detail = await getPromptDetail(id);
    setSelectedNo(id);
    setDraft(detail);
    setIsNew(false);
    setIsDirty(false);

    setDetailLoading(false);
  };

  const addNew = () => {
    setDraft({
      promptNo: '',
      name: '',
      content: '',
      type: DEFAULT_TYPE,
      description: '',
    });

    setSelectedNo(null);
    setIsNew(true);
    setIsDirty(true);
  };

  const confirmDelete = async () => {
    if (!selected) return;

    setDeleting(true); // ✅ 시작
    await deletePrompt(selected.promptNo);

    toast.success('프롬프트가 삭제되었습니다.');
    setOpenDelete(false);

    await reloadList(null);
    setDeleting(false); // ✅ 끝
  };

  const save = async () => {
    if (!(draft && (isDirty || isNew))) return;

    const payload = {
      name: draft.name?.trim(),
      type: draft.type ?? DEFAULT_TYPE,
      description:
        (draft.description && draft.description.trim()) || makeDescription(draft.content ?? ''),
      content: draft.content ?? '',
    };

    if (!payload.name) return toast.warn('이름을 입력해주세요.');
    if (!payload.content) return toast.warn('내용을 입력해주세요.');

    setSaving(true);

    if (isNew || !draft.promptNo) {
      const createdNo = await createPrompt(payload);
      toast.success('프롬프트가 생성되었습니다.');
      await reloadList(createdNo);
    } else {
      const updated = await updatePrompt(draft.promptNo, payload);
      setPrompts((prev) =>
        prev.map((p) => (p.promptNo === updated.promptNo ? { ...p, ...updated } : p))
      );
      setDraft(updated);
      setIsDirty(false);
      toast.success('프롬프트가 저장되었습니다.');
    }

    setSaving(false);
    setIsNew(false);
  };

  return (
    <>
      <div className="space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          <div className="max-w-xs w-full">
            <Select
              value={isNew ? null : selectedNo}
              onChange={(id) => handleSelect(id)}
              options={selectOptions}
              placeholder={listLoading ? '불러오는 중…' : '프롬프트 선택'}
              disabled={listLoading || prompts.length === 0}
            />
          </div>

          <button
            type="button"
            onClick={addNew}
            disabled={detailLoading || saving}
            className="btn-secondary"
          >
            <Plus className="size-4" /> 새 프롬프트
          </button>

          <button
            type="button"
            onClick={() => setOpenDelete(true)}
            disabled={isNew || !selected || detailLoading}
            className={`flex items-center gap-2 rounded-lg text-gray-700 border border-gray-200 px-3 py-2 text-sm font-medium ${
              isNew || !selected || detailLoading
                ? 'cursor-not-allowed opacity-40'
                : 'border-black text-black hover:bg-gray-50'
            }`}
          >
            <Trash2 className="size-4" /> {deleting ? '삭제 중…' : '삭제'}
          </button>

          <button
            type="button"
            onClick={save}
            disabled={!(draft && (isDirty || isNew)) || saving || detailLoading}
            className="btn-primary"
          >
            <Save className="size-4" /> {saving ? '저장 중…' : '저장'}
          </button>
        </div>

        <input
          className="input"
          value={draft?.name ?? ''}
          onChange={(e) => {
            if (!draft) return;
            setDraft((d) => ({ ...(d as Prompt), name: e.target.value }));
            setIsDirty(true);
          }}
          placeholder="프롬프트 이름"
          disabled={!draft || detailLoading}
        />

        <textarea
          className="textarea min-h-[240px]"
          value={draft?.content ?? ''}
          onChange={(e) => {
            if (!draft) return;
            const content = e.target.value;
            setDraft((d) => ({
              ...(d as Prompt),
              content,
              description: makeDescription(content),
              type: d?.type ?? DEFAULT_TYPE,
            }));
            setIsDirty(true);
          }}
          placeholder="프롬프트 내용을 입력하세요"
          disabled={!draft || detailLoading}
        />
      </div>

      <ConfirmModal
        open={openDelete}
        onClose={() => !deleting && setOpenDelete(false)}
        onConfirm={confirmDelete}
        title="프롬프트를 삭제할까요?"
        message={`"${selected?.name ?? ''}" 프롬프트를 삭제하면 되돌릴 수 없습니다.`}
        confirmText={deleting ? '삭제 중…' : '삭제'}
        cancelText="취소"
        variant="danger"
      />
    </>
  );
}
