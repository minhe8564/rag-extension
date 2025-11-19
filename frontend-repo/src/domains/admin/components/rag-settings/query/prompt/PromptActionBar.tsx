import { Plus, Save, Trash2 } from 'lucide-react';

type Props = {
  hasSelection: boolean;
  isNew: boolean;
  isEditing: boolean;
  isDirty: boolean;
  listLoading: boolean;
  detailLoading: boolean;
  saving: boolean;
  deleting: boolean;
  promptsEmpty: boolean;
  onAddNew: () => void;
  onStartEdit: () => void;
  onOpenDelete: () => void;
  onSave: () => void;
  onCancel: () => void;
};

export default function PromptActionBar({
  hasSelection,
  isNew,
  isEditing,
  isDirty,
  detailLoading,
  saving,
  deleting,
  onAddNew,
  onStartEdit,
  onOpenDelete,
  onSave,
  onCancel,
}: Props) {
  const canEdit = !isNew && !isEditing && hasSelection;
  const canDelete = !isNew && hasSelection && !detailLoading && !deleting;
  const canSave = !saving && !detailLoading && (isNew || isEditing) && (isNew || isDirty);

  return (
    <div className="flex flex-wrap items-center gap-2">
      <button
        type="button"
        onClick={onAddNew}
        disabled={detailLoading || saving}
        className={[
          'inline-flex items-center gap-2 rounded-md border px-3 py-2 text-sm font-medium transition-all',
          'border-gray-200 bg-white text-gray-800 hover:bg-gray-50',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-hebees)] focus-visible:ring-offset-1',
          'disabled:opacity-40 disabled:cursor-not-allowed',
        ].join(' ')}
      >
        <Plus className="size-4" />새 프롬프트
      </button>

      {canEdit && (
        <button
          type="button"
          onClick={onStartEdit}
          disabled={detailLoading}
          className={[
            'inline-flex items-center gap-2 rounded-md border px-3 py-2 text-sm font-medium transition-all',
            'border-gray-200 bg-white text-gray-800 hover:bg-gray-50',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-hebees)] focus-visible:ring-offset-1',
            'disabled:opacity-40 disabled:cursor-not-allowed',
          ].join(' ')}
        >
          수정
        </button>
      )}

      <button
        type="button"
        onClick={onOpenDelete}
        disabled={!canDelete}
        className={[
          'inline-flex items-center gap-2 rounded-md border px-3 py-2 text-sm font-medium transition-all',
          canDelete
            ? 'border-gray-200 bg-white text-gray-800 hover:bg-gray-50'
            : 'bg-gray-100 text-gray-400 border-gray-200 cursor-not-allowed opacity-60 pointer-events-none',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-hebees)] focus-visible:ring-offset-1',
        ].join(' ')}
      >
        <Trash2 className="size-4" />
        {deleting ? '삭제 중…' : '삭제'}
      </button>

      <button
        type="button"
        onClick={onSave}
        disabled={!canSave}
        className={[
          'inline-flex items-center gap-2 rounded-md px-3 py-2 text-sm font-semibold transition-all',
          'disabled:bg-white disabled:text-gray-400 disabled:border disabled:border-gray-200 disabled:cursor-not-allowed',
          saving
            ? 'bg-[var(--color-hebees)]/70 text-white'
            : 'bg-[var(--color-hebees)] text-white hover:opacity-90',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-hebees)] focus-visible:ring-offset-1',
        ].join(' ')}
      >
        <Save className="size-4" />
        {saving ? '저장 중…' : '저장'}
      </button>

      {(isNew || isEditing) && (
        <button
          type="button"
          onClick={onCancel}
          disabled={detailLoading || saving}
          className={[
            'inline-flex items-center gap-2 rounded-md border px-3 py-2 text-sm font-medium transition-all',
            'border-gray-200 bg-white text-gray-600 hover:bg-gray-50',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gray-300 focus-visible:ring-offset-1',
            'disabled:opacity-40 disabled:cursor-not-allowed',
          ].join(' ')}
        >
          취소
        </button>
      )}
    </div>
  );
}
