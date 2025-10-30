import Card from '@/domains/admin/components/rag-settings/ui/Card';
import { IconButton } from '@/domains/admin/components/rag-settings/ui/IconButton';
import {
  ingestTemplateOptions,
  queryTemplateOptions,
} from '@/domains/admin/components/rag-settings/options';
import { Pencil, Trash2 } from 'lucide-react';

type TemplateKind = 'ingest' | 'query';

type Props = {
  kind: TemplateKind;
  active: string;
  onSelect: (v: string) => void;
  onEdit?: (templateId: string) => void;
  onDelete?: (templateId: string) => void;
};

export function TemplateList({ kind, active, onSelect, onEdit, onDelete }: Props) {
  const options = kind === 'ingest' ? ingestTemplateOptions : queryTemplateOptions;
  const title = kind === 'ingest' ? 'Ingest 템플릿 목록' : 'Query 템플릿 목록';

  return (
    <Card title={title}>
      {options?.length ? (
        <ul className="space-y-2">
          {options.map((t: { value: string; label: string }) => {
            const isActive = active === t.value;
            return (
              <li
                key={t.value}
                className={[
                  'flex items-center justify-between rounded-md border px-3 py-2',
                  isActive
                    ? 'border-[var(--color-hebees)] bg-[var(--color-hebees-bg)]'
                    : 'bg-white hover:bg-gray-50',
                ].join(' ')}
              >
                <button
                  type="button"
                  className="truncate text-left text-sm font-medium text-gray-800"
                  onClick={() => onSelect(t.value)}
                  title={t.label}
                >
                  {t.label}
                </button>

                <div className="shrink-0 space-x-1">
                  <IconButton title="편집" onClick={() => onEdit?.(t.value)}>
                    <Pencil className="h-4 w-4" />
                  </IconButton>
                  <IconButton title="삭제" onClick={() => onDelete?.(t.value)}>
                    <Trash2 className="h-4 w-4" />
                  </IconButton>
                </div>
              </li>
            );
          })}
        </ul>
      ) : (
        <div className="text-sm text-gray-500">등록된 템플릿이 없습니다.</div>
      )}
    </Card>
  );
}
