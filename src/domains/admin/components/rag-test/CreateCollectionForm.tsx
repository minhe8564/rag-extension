import { useState } from 'react';
import type { Collection } from './types';

type Props = {
  onCancel: () => void;
  onCreate: (c: Collection) => void;
};

export function CreateCollectionForm({ onCancel, onCreate }: Props) {
  const [name, setName] = useState('');
  const [template, setTemplate] = useState('ingest-1');

  return (
    <div className="space-y-4 rounded-xl border bg-white p-4">
      <div className="text-sm font-semibold text-gray-800">새 Collection 생성</div>

      <div className="grid gap-3 sm:grid-cols-[200px_1fr] sm:items-center">
        <label className="text-sm text-gray-600">Collection 이름</label>
        <input
          className="w-full rounded-md border px-3 py-2 text-sm"
          value={name}
          onChange={e => setName(e.target.value)}
          placeholder="예: HEBEES Test"
        />
      </div>

      <div className="grid gap-3 sm:grid-cols-[200px_1fr] sm:items-center">
        <label className="text-sm text-gray-600">Ingest 템플릿</label>
        <select
          className="w-full rounded-md border px-3 py-2 text-sm"
          value={template}
          onChange={e => setTemplate(e.target.value)}
        >
          <option value="ingest-1">Ingest 템플릿 1</option>
          <option value="ingest-2">Ingest 템플릿 2</option>
        </select>
      </div>

      <div className="flex justify-end gap-2 pt-2">
        <button onClick={onCancel} className="rounded-md border px-3 py-2 text-sm hover:bg-gray-50">
          취소
        </button>
        <button
          onClick={() => onCreate({ id: crypto.randomUUID(), name, ingestTemplate: template })}
          disabled={!name.trim()}
          className="rounded-md bg-gray-900 px-3 py-2 text-sm text-white disabled:opacity-50"
        >
          생성
        </button>
      </div>
    </div>
  );
}
