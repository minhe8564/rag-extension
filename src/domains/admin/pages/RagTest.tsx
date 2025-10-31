import { useState } from 'react';
import type { Collection } from '@/domains/admin/components/rag-test/types';
import { CollectionControls } from '@/domains/admin/components/rag-test/CollectionControls';
import { EmptyState } from '@/domains/admin/components/rag-test/EmptyState';
import { CreateCollectionForm } from '@/domains/admin/components/rag-test/CreateCollectionForm';
import { SelectedCollection } from '@/domains/admin/components/rag-test/SelectedCollection';
import { RagStrategyCompare } from '@/domains/admin/components/rag-test/rag-strategy-compare/RagStrategyCompare';

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

  const selected = collections.find(c => c.id === selectedCollectionId) || null;

  const run = async () => {
    if (!selected && !creatingNew) return;
    setAnswer(`(샘플 응답) "${query}" 에 대한 RAG 결과`);
  };

  return (
    <div className="space-y-8 px-4">
      <h1 className="text-2xl">
        <span className="font-bold bg-gradient-to-r from-[#BE7DB1] to-[#81BAFF] bg-clip-text text-transparent">
          HEBEES RAG
        </span>{' '}
        <span className="font-semibold text-black">모델 테스트</span>
      </h1>

      <CollectionControls
        collections={collections}
        selectedId={selectedCollectionId}
        creatingNew={creatingNew}
        onSelect={id => {
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
          onCreate={newCol => {
            setCollections(prev => [newCol, ...prev]); // 실제로는 API 성공 후 반영
            setSelectedCollectionId(newCol.id);
            setCreatingNew(false);
          }}
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
              // 여기서 실제 API 호출로 좌/우 결과 받아서 반환하면
              // 하단 결과 박스에 즉시 표시됩니다.
              // 예시:
              // const { leftText, rightText } = await api.compareStrategies({ question, left, right, mode });
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
