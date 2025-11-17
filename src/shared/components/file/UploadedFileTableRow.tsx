import { Download, Trash2 } from 'lucide-react';
import Checkbox from '@/shared/components/controls/Checkbox';
import Tooltip from '@/shared/components/controls/Tooltip';
import FileNameCell from '@/shared/components/file/FileNameCell';
import StatusBadge from './StatusBadge';
import type { UploadedDoc } from '@/shared/types/file.types';

type RowProps = {
  doc: UploadedDoc;
  losing: boolean;
  brand: 'hebees' | 'retina';
  brandTextClass: string;
  categoryName: string;
  selected: boolean;
  onToggleSelect: (checked: boolean) => void;
  onDownload?: (id: string) => void;
  onDelete?: (ids: string[]) => void;
  onRename?: (id: string, nextName: string) => void;
  existingNames: string[];
  showStatus?: boolean;
};

export default function UploadedFileTableRow({
  doc,
  losing,
  brand,
  brandTextClass,
  categoryName,
  selected,
  onToggleSelect,
  onDownload,
  onDelete,
  onRename,
  existingNames,
  showStatus = true,
}: RowProps) {
  return (
    <tr className={`border-b last:border-b-0 ${losing ? 'bg-amber-50/40' : ''}`}>
      <td className="px-4 py-2">
        <Checkbox
          checked={selected}
          onChange={(e) => onToggleSelect(e.target.checked)}
          brand={brand}
        />
      </td>

      <td className="max-w-[260px] px-4 py-2 sm:max-w-[360px]">
        <FileNameCell
          id={doc.id}
          name={doc.name}
          losing={losing}
          brandTextClass={brandTextClass}
          onRename={onRename}
          existingNames={existingNames}
        />
      </td>

      <td className="px-4 py-2 text-right text-gray-600">
        {doc.sizeKB >= 1024
          ? `${(doc.sizeKB / 1024).toFixed(1)} MB`
          : `${doc.sizeKB.toFixed(1)} KB`}
      </td>

      <td className="px-4 py-2 text-right text-gray-600">{doc.createdAt ?? '-'}</td>

      <td className="px-4 py-2">
        <div className="flex justify-end">
          <span className="inline-flex items-center rounded-full border border-gray-300 px-3 py-1 text-xs text-gray-700">
            {categoryName}
          </span>
        </div>
      </td>

      {showStatus && (
        <td className="px-4 py-2 text-right">
          <StatusBadge status={doc.status} />
        </td>
      )}

      <td>
        <div className="flex items-center justify-end gap-1.5">
          <Tooltip content="다운로드" side="bottom" offset={1}>
            <button
              className="rounded-md p-2 hover:bg-gray-50"
              onClick={() => onDownload?.(doc.id)}
            >
              <Download size={16} />
            </button>
          </Tooltip>

          <Tooltip
            content={losing ? '이 항목만 삭제하여 최신만 남기기' : '삭제'}
            side="bottom"
            offset={1}
          >
            <button
              className="rounded-md p-2 text-red-600 hover:bg-red-50"
              onClick={() => onDelete?.([doc.id])}
            >
              <Trash2 size={16} />
            </button>
          </Tooltip>
        </div>
      </td>
    </tr>
  );
}
