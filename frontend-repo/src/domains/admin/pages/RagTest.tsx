import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import type { Collection } from '@/domains/admin/components/rag-test/types';
import { CollectionControls } from '@/domains/admin/components/rag-test/CollectionControls';
import { EmptyState } from '@/domains/admin/components/rag-test/EmptyState';
import { CreateCollectionForm } from '@/domains/admin/components/rag-test/CreateCollectionForm';
import { SelectedCollection } from '@/domains/admin/components/rag-test/SelectedCollection';
import { RagStrategyCompare } from '@/domains/admin/components/rag-test/rag-strategy-compare/RagStrategyCompare';
import { Bot } from 'lucide-react';

import { makeRagOptions, type RagOptions } from '@/domains/admin/components/rag-settings/options';
import { getStrategies } from '@/domains/admin/api/rag-settings/strategies.api';

const mockCollections: Collection[] = [
  { id: 'c1', name: 'HEBEES Test', ingestTemplate: 'ingest-기본' },
  { id: 'c2', name: 'Finance Doc Set', ingestTemplate: 'ingest-텐서' },
];

export default function RagTest() {
  const [collections, setCollections] = useState<Collection[]>(mockCollections);
  const [selectedCollectionId, setSelectedCollectionId] = useState<string | null>(null);
  const [creatingNew, setCreatingNew] = useState(false);

  const [query, setQuery] = useState('');
  const [answer, setAnswer] = useState<string | null>(null);

  const selected = collections.find((c) => c.id === selectedCollectionId) || null;

  const {
    data: strategies,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ['rag-strategies'],
    queryFn: () => getStrategies(), // returns Strategy[]
    staleTime: 60_000,
  });

  const options: RagOptions | null = useMemo(
    () => (strategies ? makeRagOptions(strategies) : null),
    [strategies]
  );

  const run = async () => {
    if (!selected && !creatingNew) return;
    setAnswer(`(샘플 응답) "${query}" 에 대한 RAG 결과`);
  };

  return (
    <div className="space-y-8 px-4 mb-20">
      <div className="flex items-center gap-3">
        <div className="p-3 rounded-xl bg-gradient-to-r from-[#EED8F3]/70 to-[#CBE1FF]/70 flex items-center justify-center">
          <Bot size={28} className="text-[var(--color-hebees)]" />
        </div>
        <div>
          <h1 className="text-2xl font-semibold">
            <span className="font-bold bg-gradient-to-r from-[#BE7DB1] to-[#81BAFF] bg-clip-text text-transparent">
              HEBEES RAG
            </span>{' '}
            <span className="font-semibold text-black">모델 테스트</span>
          </h1>
          <p className="text-sm text-gray-600">
            RAG 모델을 테스트하고 응답 품질을 확인할 수 있습니다.
          </p>
        </div>
      </div>

      <CollectionControls
        collections={collections}
        selectedId={selectedCollectionId}
        creatingNew={creatingNew}
        onSelect={(id) => {
          setSelectedCollectionId(id);
          setCreatingNew(false);
          setAnswer(null);
        }}
        onCreateNew={() => {
          setCreatingNew(true);
          setSelectedCollectionId(null);
          setAnswer(null);
        }}
      />

      {!selected && !creatingNew && <EmptyState />}

      {creatingNew && !selected && (
        <CreateCollectionForm
          onCancel={() => setCreatingNew(false)}
          onCreate={(newCol) => {
            setCollections((prev) => [newCol, ...prev]);
            setSelectedCollectionId(newCol.id);
            setCreatingNew(false);
          }}
          options={options}
          loadingOptions={isLoading}
          optionsError={isError}
        />
      )}

      {selected && !creatingNew && (
        <>
          <SelectedCollection
            collection={selected}
            query={query}
            setQuery={setQuery}
            run={run}
            answer={answer}
          />

          <RagStrategyCompare
            onRunCompare={async ({ question, left, right, mode }) => {
              return {
                left: `[${mode}] ${left.ingest?.name ?? '-'} × ${left.query?.name ?? '-'}\nQ: ${question}\n→ 좌측 실제 응답…`,
                right: `[${mode}] ${right.ingest?.name ?? '-'} × ${right.query?.name ?? '-'}\nQ: ${question}\n→ 우측 실제 응답…`,
              };
            }}
          />
        </>
      )}
    </div>
  );
}
