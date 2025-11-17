import Select from '@/shared/components/controls/Select';
import ConfirmModal from '@/shared/components/ConfirmModal';
import PromptForm from '@/domains/admin/components/rag-settings/query/prompt/PromptForm';
import PromptView from '@/domains/admin/components/rag-settings/query/prompt/PromptView';
import PromptActionBar from '@/domains/admin/components/rag-settings/query/prompt/PromptActionBar';
import { usePromptManager } from '@/domains/admin/hooks/usePromptManager';
import type { Prompt, PromptType } from '@/domains/admin/types/rag-settings/prompts.types';

type Props = {
  initialPrompts?: Array<{ id: string; name: string; content: string; type?: PromptType }>;
  onChange?: (prompts: Prompt[]) => void;
};

export default function PromptManager({ initialPrompts, onChange }: Props) {
  const {
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
    handleSelect,
    addNew,
    startEdit,
    cancelEdit,
    confirmDelete,
    save,
  } = usePromptManager(initialPrompts, onChange);

  return (
    <>
      <div className="flex flex-wrap items-center gap-2">
        <div className="max-w-xs w-full">
          <Select
            value={isNew ? null : selectedNo}
            onChange={handleSelect}
            options={selectOptions}
            placeholder={listLoading ? '불러오는 중…' : '프롬프트 선택'}
            disabled={listLoading || prompts.length === 0}
          />
        </div>

        <PromptActionBar
          hasSelection={!!selected}
          isNew={isNew}
          isEditing={isEditing}
          isDirty={isDirty}
          listLoading={listLoading}
          detailLoading={detailLoading}
          saving={saving}
          deleting={deleting}
          promptsEmpty={prompts.length === 0}
          onAddNew={addNew}
          onStartEdit={startEdit}
          onOpenDelete={() => setOpenDelete(true)}
          onSave={save}
          onCancel={cancelEdit}
        />
      </div>

      {isNew || isEditing ? (
        <PromptForm
          draft={draft}
          disabled={!draft || detailLoading}
          makeDescription={(s) => s.replace(/\s+/g, ' ').slice(0, 120)}
          onChangeDraft={setDraft}
          onDirty={() => setIsDirty(true)}
        />
      ) : (
        <PromptView selected={selected} draft={draft} />
      )}

      <ConfirmModal
        open={openDelete}
        onClose={() => !deleting && setOpenDelete(false)}
        onConfirm={confirmDelete}
        title="프롬프트를 삭제할까요?"
        message={`"${selected?.name ?? ''}" 프롬프트를\n삭제하면 되돌릴 수 없습니다.`}
        confirmText={deleting ? '삭제 중…' : '삭제'}
        cancelText="취소"
        variant="danger"
      />
    </>
  );
}
