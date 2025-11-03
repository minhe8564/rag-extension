import Card from '@/shared/components/Card';
import Select from '@/shared/components/Select';
import { Plus } from 'lucide-react';

export type Collection = {
  id: string;
  name: string;
  ingestTemplate?: string;
};

type Props = {
  title?: string;
  subtitle?: string;
  collections: Collection[];
  selectedId: string | null;
  creatingNew?: boolean;
  onSelect: (id: string | null) => void;
  onCreateNew: () => void;
  className?: string;
};

export function CollectionControls({
  title = 'Collection 확인',
  subtitle = 'RAG 모델을 테스트할 Collection 내 문서를 확인해주세요.',
  collections,
  selectedId,
  creatingNew = false,
  onSelect,
  onCreateNew,
  className = '',
}: Props) {
  return (
    <Card title={title} subtitle={subtitle} className={className}>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="sm:w-[360px]">
          <Select
            value={selectedId ?? ''}
            onChange={(value: string) => onSelect(value || null)}
            options={[
              { label: '기존 Collection 선택', value: '' },
              ...collections.map(c => ({
                label: `${c.name}${c.ingestTemplate ? ` · [${c.ingestTemplate}]` : ''}`,
                value: c.id,
              })),
            ]}
          />
        </div>

        <div className="flex flex-1 items-center gap-2">
          <button
            type="button"
            className="inline-flex items-center gap-1.5 rounded-md border px-3 py-2 text-sm hover:bg-gray-50"
            onClick={onCreateNew}
          >
            <Plus size={14} className="text-gray-700" />새 Collection 추가하기
          </button>

          {!selectedId && !creatingNew && (
            <span className="ml-auto inline-flex items-center gap-2 rounded-md bg-[#f7e8f3] px-3 py-1.5 text-xs text-[#8a2e6e]">
              <span className="inline-block h-2 w-2 rounded-full bg-[#BE7DB1]" />
              Collection을 선택하거나 새로 만들어주세요.
            </span>
          )}
        </div>
      </div>
    </Card>
  );
}
