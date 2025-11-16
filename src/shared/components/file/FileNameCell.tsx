import { useState } from 'react';
import { FileText, AlertTriangle, Check, X, Edit3 } from 'lucide-react';
import Tooltip from '@/shared/components/controls/Tooltip';
import { ensureUniqueName } from '@/shared/utils/fileName';

export type FileNameCellProps = {
  id: string;
  name: string;
  losing: boolean;
  brandTextClass: string;
  onRename?: (id: string, nextName: string) => void;
  existingNames: string[];
};

export default function FileNameCell({
  id,
  name,
  losing,
  brandTextClass,
  onRename,
  existingNames,
}: FileNameCellProps) {
  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState(name);

  const commit = () => {
    if (!onRename) return setEditing(false);
    const trimmed = value.trim();
    if (!trimmed || trimmed === name) {
      setEditing(false);
      setValue(name);
      return;
    }
    const setNames = new Set(existingNames);
    const unique = ensureUniqueName(trimmed, setNames);
    onRename(id, unique);
    setEditing(false);
  };

  if (editing) {
    return (
      <div className="min-w-0 flex flex-1 items-center gap-2">
        <input
          autoFocus
          className="
    min-w-0 flex-1 rounded-md border px-2.5 py-1,5 text-sm
    border-gray-300
    focus:border-gray-400
    focus:ring-0
    focus:outline-none
  "
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') commit();
            if (e.key === 'Escape') {
              setEditing(false);
              setValue(name);
            }
          }}
        />
        <button className="rounded-md p-1 hover:bg-gray-50" onClick={commit}>
          <Check size={16} />
        </button>
        <button
          className="rounded-md p-1 hover:bg-gray-50"
          onClick={() => {
            setEditing(false);
            setValue(name);
          }}
        >
          <X size={16} />
        </button>
      </div>
    );
  }

  return (
    <div className="min-w-0 flex items-center gap-2">
      <div className="flex h-4 w-4 shrink-0 items-center justify-center">
        <FileText size={16} className={brandTextClass} />
      </div>
      <span className="min-w-0 flex-1">
        <span className="block w-full truncate text-sm text-gray-800">{name}</span>
        {losing && (
          <span className="mt-0.5 inline-flex items-center gap-1 text-[11px] text-amber-600">
            <AlertTriangle size={12} /> 중복 이름 (최신 아님)
          </span>
        )}
      </span>

      {losing && onRename && (
        <Tooltip content="이름 바꾸기" side="bottom" offset={1}>
          <button
            className="rounded-md p-2 hover:bg-white"
            onClick={() => {
              setValue(name);
              setEditing(true);
            }}
          >
            <Edit3 size={16} />
          </button>
        </Tooltip>
      )}
    </div>
  );
}
