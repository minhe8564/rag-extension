import { useEffect, useMemo, useState } from 'react';
import { toast } from 'react-toastify';
import type { Prompt, PromptType } from '@/domains/admin/types/rag-settings/prompts.types';
import {
  getPrompts,
  getPromptDetail,
  createPrompt,
  updatePrompt,
  deletePrompt,
} from '@/domains/admin/api/rag-settings/prompts.api';

const DEFAULT_TYPE: PromptType = 'user';
export const makeDescription = (content: string, max = 120) =>
  (content ?? '').replace(/\s+/g, ' ').slice(0, max);

export function usePromptManager(
  initialPrompts?: Array<{ id: string; name: string; content: string; type?: PromptType }>,
  onChange?: (prompts: Prompt[]) => void
) {
  const [prompts, setPrompts] = useState<Prompt[]>(
    (initialPrompts ?? []).map((p) => ({
      promptNo: p.id,
      name: p.name,
      content: p.content,
      type: p.type ?? DEFAULT_TYPE,
      description: makeDescription(p.content),
    }))
  );
  const [selectedNo, setSelectedNo] = useState<string | null>(prompts[0]?.promptNo ?? null);
  const [draft, setDraft] = useState<Prompt | null>(prompts[0] ?? null);

  const [isNew, setIsNew] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [isDirty, setIsDirty] = useState(false);

  const [openDelete, setOpenDelete] = useState(false);
  const [listLoading, setListLoading] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const reloadList = async (selectAfter?: string | null) => {
    setListLoading(true);
    const { data } = await getPrompts({ pageNum: 1, pageSize: 20 });
    setPrompts(data);
    onChange?.(data);

    const nextId = selectAfter ?? data[0]?.promptNo ?? null;
    setSelectedNo(nextId);

    if (nextId) {
      const detail = await getPromptDetail(nextId);
      setDraft(detail);
      setIsEditing(false);
      setIsNew(false);
      setIsDirty(false);
    } else {
      setDraft(null);
      setIsEditing(false);
      setIsNew(false);
      setIsDirty(false);
    }
    setListLoading(false);
  };

  useEffect(() => {
    void reloadList(selectedNo ?? undefined);
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
    setIsEditing(false);
    setIsDirty(false);
    setDetailLoading(false);
  };

  const addNew = () => {
    setDraft({ promptNo: '', name: '', content: '', type: DEFAULT_TYPE, description: '' });
    setSelectedNo(null);
    setIsNew(true);
    setIsEditing(true);
    setIsDirty(true);
  };

  const startEdit = () => {
    if (!selected) return;
    setIsEditing(true);
    setIsNew(false);
  };

  const cancelEdit = () => {
    if (isNew) {
      setIsNew(false);
      setIsEditing(false);
      setIsDirty(false);
      if (prompts[0]) {
        setSelectedNo(prompts[0].promptNo);
        getPromptDetail(prompts[0].promptNo).then((d) => setDraft(d));
      } else {
        setSelectedNo(null);
        setDraft(null);
      }
      return;
    }
    if (selectedNo) {
      getPromptDetail(selectedNo).then((d) => setDraft(d));
    }
    setIsEditing(false);
    setIsDirty(false);
  };

  const confirmDelete = async () => {
    if (!selected) return;
    setDeleting(true);
    await deletePrompt(selected.promptNo);
    toast.success('프롬프트가 삭제되었습니다.');
    setOpenDelete(false);
    await reloadList(null);
    setDeleting(false);
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
      setIsEditing(false);
      toast.success('프롬프트가 저장되었습니다.');
    }
    setSaving(false);
    setIsNew(false);
  };

  return {
    prompts,
    selectedNo,
    draft,
    isNew,
    isEditing,
    isDirty,
    openDelete,
    listLoading,
    detailLoading,
    saving,
    deleting,
    selected,
    selectOptions,

    setDraft,
    setIsDirty,
    setOpenDelete,

    reloadList,
    handleSelect,
    addNew,
    startEdit,
    cancelEdit,
    confirmDelete,
    save,
  };
}
